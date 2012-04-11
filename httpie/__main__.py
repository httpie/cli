#!/usr/bin/env python
import sys
import json
try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict
import requests
from requests.compat import urlparse, str
from requests.structures import CaseInsensitiveDict
from . import cli
from . import pretty
from . import __version__ as version


NEW_LINE = str('\n')
DEFAULT_UA = 'HTTPie/%s' % version
TYPE_FORM = 'application/x-www-form-urlencoded; charset=utf-8'
TYPE_JSON = 'application/json; charset=utf-8'


class HTTPMessage(object):

    def __init__(self, line, headers, body, content_type=None):
        # {Request,Status}-Line
        self.line = line
        self.headers = headers
        self.body = body
        self.content_type = content_type


def format_http_message(message, prettifier=None,
                        with_headers=True, with_body=True):
    bits = []
    if with_headers:
        if prettifier:
            bits.append(prettifier.headers(message.line))
            bits.append(prettifier.headers(message.headers))
        else:
            bits.append(message.line)
            bits.append(message.headers)
        if with_body and message.body:
            bits.append(NEW_LINE)
    if with_body and message.body:
        if prettifier and message.content_type:
            bits.append(prettifier.body(message.body, message.content_type))
        else:
            bits.append(message.body)
    bits.append(NEW_LINE)
    return NEW_LINE.join(bit.strip() for bit in bits)


def make_request_message(request):
    """Make an `HTTPMessage` from `requests.models.Request`."""
    url = urlparse(request.url)
    request_headers = dict(request.headers)
    if 'Host' not in request_headers:
        request_headers['Host'] = url.netloc
    return HTTPMessage(
        line='{method} {path} HTTP/1.1'.format(
                method=request.method,
                path=url.path or '/'),
        headers=NEW_LINE.join(str('%s: %s') % (name, value)
                          for name, value
                          in request_headers.items()),
        body=request._enc_data,
        content_type=request_headers.get('Content-Type')
    )


def make_response_message(response):
    """Make an `HTTPMessage` from `requests.models.Response`."""
    encoding = response.encoding or 'ISO-8859-1'
    original = response.raw._original_response
    response_headers = response.headers
    return HTTPMessage(
        line='HTTP/{version} {status} {reason}'.format(
                version='.'.join(str(original.version)),
                status=original.status, reason=original.reason,),
        headers=str(original.msg),
        body=response.content.decode(encoding) if response.content else '',
        content_type=response_headers.get('Content-Type'))


def main(args=None,
         stdin=sys.stdin,
         stdin_isatty=sys.stdin.isatty(),
         stdout=sys.stdout,
         stdout_isatty=sys.stdout.isatty()):

    parser = cli.parser

    args = parser.parse_args(args if args is not None else sys.argv[1:])
    do_prettify = (args.prettify is True or
                   (args.prettify == cli.PRETTIFY_STDOUT_TTY_ONLY
                    and stdout_isatty))

    # Parse request headers and data from the command line.
    headers = CaseInsensitiveDict()
    headers['User-Agent'] = DEFAULT_UA
    data = OrderedDict()
    files = OrderedDict()
    try:
        cli.parse_items(items=args.items, headers=headers,
                        data=data, files=files)
    except cli.ParseError as e:
        if args.traceback:
            raise
        parser.error(e.message)

    if files and not args.form:
        # We could just switch to --form automatically here,
        # but I think it's better to make it explicit.
        parser.error(
            ' You need to set the --form / -f flag to'
            ' to issue a multipart request. File fields: %s'
            % ','.join(files.keys()))

    if not stdin_isatty:
        if data:
            parser.error('Request body (stdin) and request '
                                'data (key=value) cannot be mixed.')
        data = stdin.read()

    # JSON/Form content type.
    if args.json or (not args.form and data):
        if stdin_isatty:
            data = json.dumps(data)
        if not files and ('Content-Type' not in headers and (data or args.json)):
            headers['Content-Type'] = TYPE_JSON
    elif not files and 'Content-Type' not in headers:
        headers['Content-Type'] = TYPE_FORM

    # Fire the request.
    try:
        credentials = None
        if args.auth and args.digest:
            credentials = requests.auth.HTTPDigestAuth(args.auth.key, args.auth.value)
        elif args.auth:
            credentials = requests.auth.HTTPBasicAuth(args.auth.key, args.auth.value)

        response = requests.request(
            method=args.method.lower(),
            url=args.url if '://' in args.url else 'http://%s' % args.url,
            headers=headers,
            data=data,
            verify={'yes': True, 'no': False}.get(args.verify, args.verify),
            timeout=args.timeout,
            auth=credentials,
            proxies=dict((p.key, p.value) for p in args.proxy),
            files=files,
            allow_redirects=args.allow_redirects,
        )
    except (KeyboardInterrupt, SystemExit):
        sys.stderr.write(NEW_LINE)
        sys.exit(1)
    except Exception as e:
        if args.traceback:
            raise
        sys.stderr.write(str(e.message) + NEW_LINE)
        sys.exit(1)

    prettifier = pretty.PrettyHttp(args.style) if do_prettify else None

    output_request = (cli.OUT_REQUEST_HEADERS in args.output_options
                      or cli.OUT_REQUEST_BODY in args.output_options)

    output_response = (cli.OUT_RESPONSE_HEADERS in args.output_options
                      or cli.OUT_RESPONSE_BODY in args.output_options)

    if output_request:
        stdout.write(format_http_message(
            message=make_request_message(response.request),
            prettifier=prettifier,
            with_headers=cli.OUT_REQUEST_HEADERS in args.output_options,
            with_body=cli.OUT_REQUEST_BODY in args.output_options
        ))
        if output_response:
            stdout.write(NEW_LINE)

    if output_response:
        stdout.write(format_http_message(
            message=make_response_message(response),
            prettifier=prettifier,
            with_headers=cli.OUT_RESPONSE_HEADERS in args.output_options,
            with_body=cli.OUT_RESPONSE_BODY in args.output_options
        ))
        stdout.write(NEW_LINE)


if __name__ == '__main__':
    main()
