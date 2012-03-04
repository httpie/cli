#!/usr/bin/env python
import os
import sys
import json
import requests
try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict
from requests.structures import CaseInsensitiveDict
from . import cli
from . import pretty
from . import __version__ as version


DEFAULT_UA = 'HTTPie/%s' % version
TYPE_FORM = 'application/x-www-form-urlencoded; charset=utf-8'
TYPE_JSON = 'application/json; charset=utf-8'


def main(args=None,
         stdin=sys.stdin,
         stdin_isatty=sys.stdin.isatty(),
         stdout=sys.stdout,
         stdout_isatty=sys.stdout.isatty()):

    parser = cli.parser

    args = parser.parse_args(args if args is not None else sys.argv[1:])
    do_prettify = (args.prettify is True or
                     (args.prettify == cli.PRETTIFY_STDOUT_TTY_ONLY and stdout_isatty))

    # Parse request headers and data from the command line.
    headers = CaseInsensitiveDict()
    headers['User-Agent'] = DEFAULT_UA
    data = OrderedDict()
    try:
        cli.parse_items(items=args.items, headers=headers, data=data)
    except cli.ParseError as e:
        if args.traceback:
            raise
        parser.error(e.message)

    if not stdin_isatty:
        if data:
            parser.error('Request body (stdin) and request '
                                'data (key=value) cannot be mixed.')
        data = stdin.read()

    # JSON/Form content type.
    if args.json or (not args.form and data):
        if stdin_isatty:
            data = json.dumps(data)
        if 'Content-Type' not in headers and (data or args.json):
            headers['Content-Type'] = TYPE_JSON
    elif 'Content-Type' not in headers:
        headers['Content-Type'] = TYPE_FORM

    # Fire the request.
    try:
        response = requests.request(
            method=args.method.lower(),
            url=args.url if '://' in args.url else 'http://%s' % args.url,
            headers=headers,
            data=data,
            verify=True if args.verify == 'yes' else args.verify,
            timeout=args.timeout,
            auth=(args.auth.key, args.auth.value) if args.auth else None,
            proxies=dict((p.key, p.value) for p in args.proxy),
            files=dict((os.path.basename(f.name), f) for f in args.file),
            allow_redirects=args.allow_redirects,
        )
    except (KeyboardInterrupt, SystemExit):
        sys.stderr.write('\n')
        sys.exit(1)
    except Exception as e:
        if args.traceback:
            raise
        sys.stderr.write(str(e.message) + '\n')
        sys.exit(1)

    # Reconstruct the raw response.
    encoding = response.encoding or 'ISO-8859-1'
    original = response.raw._original_response
    status_line, headers, body = (
        'HTTP/{version} {status} {reason}'.format(
            version='.'.join(str(original.version)),
            status=original.status, reason=original.reason,
        ),
        str(original.msg).decode(encoding),
        response.content.decode(encoding) if response.content else u''
    )

    if do_prettify:
        prettify = pretty.PrettyHttp(args.style)
        if args.print_headers:
            status_line = prettify.headers(status_line)
            headers = prettify.headers(headers)
        if args.print_body and 'Content-Type' in response.headers:
            body = prettify.body(body, response.headers['Content-Type'])

    # Output.
    # TODO: preserve leading/trailing whitespaces in the body.
    #        Some of the Pygments styles add superfluous line breaks.
    if args.print_headers:
        stdout.write(status_line.strip())
        stdout.write('\n')
        stdout.write(headers.strip().encode('utf-8'))
        stdout.write('\n\n')
    if args.print_body:
        stdout.write(body.strip().encode('utf-8'))
        stdout.write('\n')


if __name__ == '__main__':
    main()
