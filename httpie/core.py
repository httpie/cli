"""This module provides the main functionality of HTTPie.

Invocation flow:

    1. Read, validate and process the input (args, `stdin`).
    2. Create a request and send it, get the response.
    3. Process and format the requested parts of the request-response exchange.
    4. Write to `stdout` and exit.

"""
import sys
import json

import requests
import requests.auth
from requests.compat import str

from .models import HTTPRequest, HTTPResponse, Environment
from .output import OutputProcessor, formatted_stream
from .input import (OUT_REQ_BODY, OUT_REQ_HEAD,
                    OUT_RESP_HEAD, OUT_RESP_BODY)
from .cli import parser


FORM = 'application/x-www-form-urlencoded; charset=utf-8'
JSON = 'application/json; charset=utf-8'
HTTP = 'http://'
HTTPS = 'https://'


def get_response(args, env):
    """Send the request and return a `request.Response`."""

    auto_json = args.data and not args.form
    if args.json or auto_json:
        if 'Content-Type' not in args.headers:
            args.headers['Content-Type'] = JSON

        if 'Accept' not in args.headers:
            # Default Accept to JSON as well.
            args.headers['Accept'] = 'application/json'

        if isinstance(args.data, dict):
            # If not empty, serialize the data `dict` parsed from arguments.
            # Otherwise set it to `None` avoid sending "{}".
            args.data = json.dumps(args.data) if args.data else None

    elif args.form:
        if not args.files and 'Content-Type' not in args.headers:
            # If sending files, `requests` will set
            # the `Content-Type` for us.
            args.headers['Content-Type'] = FORM

    credentials = None
    if args.auth:
        credentials = {
            'basic': requests.auth.HTTPBasicAuth,
            'digest': requests.auth.HTTPDigestAuth,
        }[args.auth_type](args.auth.key, args.auth.value)

    if not (args.url.startswith(HTTP) or args.url.startswith(HTTPS)):
        scheme = HTTPS if env.progname == 'https' else HTTP
        url = scheme + args.url
    else:
        url = args.url

    return requests.request(
        method=args.method.lower(),
        url=url,
        headers=args.headers,
        data=args.data,
        verify={'yes': True, 'no': False}.get(args.verify, args.verify),
        timeout=args.timeout,
        auth=credentials,
        proxies=dict((p.key, p.value) for p in args.proxy),
        files=args.files,
        allow_redirects=args.allow_redirects,
        params=args.params,
    )


def output_stream(args, env, request, response):
    """Format parts of the `request`-`response` exchange
     according to `args` and `env` and return `bytes`.

    """

    prettifier = (OutputProcessor(env, pygments_style=args.style)
                  if args.prettify else None)

    with_request = (OUT_REQ_HEAD in args.output_options
                    or OUT_REQ_BODY in args.output_options)
    with_response = (OUT_RESP_HEAD in args.output_options
                     or OUT_RESP_BODY in args.output_options)

    if with_request:
        request_iter = formatted_stream(
            msg=HTTPRequest(request),
            env=env,
            prettifier=prettifier,
            with_headers=OUT_REQ_HEAD in args.output_options,
            with_body=OUT_REQ_BODY in args.output_options)

        for chunk in request_iter:
            yield chunk

    if with_request and with_response:
        yield b'\n\n\n'

    if with_response:
        response_iter = formatted_stream(
            msg=HTTPResponse(response),
            env=env,
            prettifier=prettifier,
            with_headers=OUT_RESP_HEAD in args.output_options,
            with_body=OUT_RESP_BODY in args.output_options)

        for chunk in response_iter:
            yield chunk

    if env.stdout_isatty:
        yield b'\n\n'


def get_exist_status(code, allow_redirects=False):
    """Translate HTTP status code to exit status."""
    if 300 <= code <= 399 and not allow_redirects:
        # Redirect
        return 3
    elif 400 <= code <= 499:
        # Client Error
        return 4
    elif 500 <= code <= 599:
        # Server Error
        return 5
    else:
        return 0


def main(args=sys.argv[1:], env=Environment()):
    """Run the main program and write the output to ``env.stdout``.

    Return exit status.

    """

    if env.is_windows and not env.stdout_isatty:
        env.stderr.write(
            'http: error: Output redirection is not supported on Windows.'
            ' Please use `--output FILE\' instead.\n')
        return 1

    try:
        args = parser.parse_args(args=args, env=env)
        response = get_response(args, env)
        status = 0

        if args.check_status:
            status = get_exist_status(response.status_code,
                                      args.allow_redirects)
            if status and not env.stdout_isatty:
                err = 'http error: %s %s\n' % (
                    response.raw.status, response.raw.reason)
                env.stderr.write(err)

        try:
            # We are writing bytes so we use buffer on Python 3
            buffer = env.stdout.buffer
        except AttributeError:
            buffer = env.stdout

        for chunk in output_stream(args, env, response.request, response):
            buffer.write(chunk)
            if env.stdout_isatty:
                env.stdout.flush()

    except (KeyboardInterrupt, SystemExit):
        env.stderr.write('\n')
        return 1
    except Exception as e:
        if '--debug' in args:
            raise
        env.stderr.write(str(repr(e) + '\n'))
        return 1

    return status
