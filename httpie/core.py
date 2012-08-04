"""This module provides the main functionality of HTTPie.

Invocation flow:

    1. Read, validate and process the input (args, `stdin`).
    2. Create and send a request.
    3. Stream, and possibly process and format, the requested parts
       of the request-response exchange.
    4. Simultaneously write to `stdout`
    5. Exit.

"""
import sys
import json
import errno
from itertools import chain
from functools import partial

import requests
import requests.auth
from requests.compat import str

from .models import HTTPRequest, HTTPResponse, Environment
from .output import (OutputProcessor, RawStream, PrettyStream,
                     BufferedPrettyStream, EncodedStream)

from .input import (OUT_REQ_BODY, OUT_REQ_HEAD,
                    OUT_RESP_HEAD, OUT_RESP_BODY)
from .cli import parser


FORM = 'application/x-www-form-urlencoded; charset=utf-8'
JSON = 'application/json; charset=utf-8'


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

    return requests.request(
        method=args.method.lower(),
        url=args.url,
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

    # Pick the right stream type for this exchange based on `env` and `args`.
    if not env.stdout_isatty and not args.prettify:
        Stream = partial(
            RawStream,
            chunk_size=RawStream.CHUNK_SIZE_BY_LINE
                       if args.stream
                       else RawStream.CHUNK_SIZE)
    elif args.prettify:
        Stream = partial(
            PrettyStream if args.stream else BufferedPrettyStream,
            processor=OutputProcessor(env, pygments_style=args.style),
            env=env)
    else:
        Stream = partial(EncodedStream, env=env)

    req_h = OUT_REQ_HEAD in args.output_options
    req_b = OUT_REQ_BODY in args.output_options
    resp_h = OUT_RESP_HEAD in args.output_options
    resp_b = OUT_RESP_BODY  in args.output_options

    req = req_h or req_b
    resp = resp_h or resp_b

    output = []

    if req:
        output.append(Stream(
            msg=HTTPRequest(request),
            with_headers=req_h,
            with_body=req_b))

    if req and resp:
        output.append([b'\n\n\n'])

    if resp:
        output.append(Stream(
            msg=HTTPResponse(response),
            with_headers=resp_h,
            with_body=resp_b))

    if env.stdout_isatty:
        output.append([b'\n\n'])

    return chain(*output)


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
    debug = '--debug' in args

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

        try:
            for chunk in output_stream(args, env, response.request, response):
                buffer.write(chunk)
                if env.stdout_isatty or args.stream:
                    env.stdout.flush()

        except IOError as e:
            if debug:
                raise
            if e.errno == errno.EPIPE:
                env.stderr.write('\n')
            else:
                env.stderr.write(str(e) + '\n')
            return 1

    except (KeyboardInterrupt, SystemExit):
        if debug:
            raise
        env.stderr.write('\n')
        return 1
    except Exception as e:
        if debug:
            raise
        env.stderr.write(str(e) + '\n')
        return 1

    return status
