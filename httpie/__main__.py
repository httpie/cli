#!/usr/bin/env python
import sys
import json

import requests

from requests.compat import str

from . import httpmessage
from . import cliparse
from . import cli
from . import pretty


TYPE_FORM = 'application/x-www-form-urlencoded; charset=utf-8'
TYPE_JSON = 'application/json; charset=utf-8'


def _get_response(args):

    auto_json = args.data and not args.form
    if args.json or auto_json:
        # JSON
        if 'Content-Type' not in args.headers:
            args.headers['Content-Type'] = TYPE_JSON

        if 'Accept' not in args.headers:
            # Default Accept to JSON as well.
            args.headers['Accept'] = 'application/json'

        if isinstance(args.data, dict):
            # If not empty, serialize the data `dict` parsed from arguments.
            # Otherwise set it to `None` avoid sending "{}".
            args.data = json.dumps(args.data) if args.data else None

    elif args.form:
        # Form
        if not args.files and 'Content-Type' not in args.headers:
            # If sending files, `requests` will set
            # the `Content-Type` for us.
            args.headers['Content-Type'] = TYPE_FORM

    # Fire the request.
    try:
        credentials = None
        if args.auth:
            auth_type = (requests.auth.HTTPDigestAuth
                         if args.auth_type == 'digest'
                         else requests.auth.HTTPBasicAuth)
            credentials = auth_type(args.auth.key, args.auth.value)

        return requests.request(
            method=args.method.lower(),
            url=args.url if '://' in args.url else 'http://%s' % args.url,
            headers=args.headers,
            data=args.data,
            verify={'yes': True, 'no': False}.get(args.verify, args.verify),
            timeout=args.timeout,
            auth=credentials,
            proxies=dict((p.key, p.value) for p in args.proxy),
            files=args.files,
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


def _get_output(args, stdout_isatty, response):

    do_prettify = (args.prettify is True or
                   (args.prettify == cliparse.PRETTIFY_STDOUT_TTY_ONLY
                    and stdout_isatty))

    do_output_request = (cliparse.OUT_REQ_HEADERS in args.output_options
                         or cliparse.OUT_REQ_BODY in args.output_options)

    do_output_response = (cliparse.OUT_RESP_HEADERS in args.output_options
                          or cliparse.OUT_RESP_BODY in args.output_options)

    prettifier = pretty.PrettyHttp(args.style) if do_prettify else None
    output = []

    if do_output_request:
        output.append(httpmessage.format(
            message=httpmessage.from_request(response.request),
            prettifier=prettifier,
            with_headers=cliparse.OUT_REQ_HEADERS in args.output_options,
            with_body=cliparse.OUT_REQ_BODY in args.output_options
        ))
        output.append('\n')
        if do_output_response:
            output.append('\n')

    if do_output_response:
        output.append(httpmessage.format(
            message=httpmessage.from_response(response),
            prettifier=prettifier,
            with_headers=cliparse.OUT_RESP_HEADERS in args.output_options,
            with_body=cliparse.OUT_RESP_BODY in args.output_options
        ))
        output.append('\n')

    return ''.join(output)


def main(args=None,
         stdin=sys.stdin, stdin_isatty=sys.stdin.isatty(),
         stdout=sys.stdout, stdout_isatty=sys.stdout.isatty()):
    parser = cli.parser
    args = parser.parse_args(
        args=args if args is not None else sys.argv[1:],
        stdin=stdin,
        stdin_isatty=stdin_isatty
    )
    response = _get_response(args)
    output = _get_output(args, stdout_isatty, response)
    output_bytes = output.encode('utf8')
    f = (stdout.buffer if hasattr(stdout, 'buffer') else stdout)
    f.write(output_bytes)


if __name__ == '__main__':
    main()
