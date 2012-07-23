import sys
import json
import requests
from requests.compat import str
from .models import HTTPMessage, Environment
from .output import OutputProcessor
from . import cliparse
from . import cli


TYPE_FORM = 'application/x-www-form-urlencoded; charset=utf-8'
TYPE_JSON = 'application/json; charset=utf-8'


def get_response(args):

    auto_json = args.data and not args.form
    if args.json or auto_json:
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
        if not args.files and 'Content-Type' not in args.headers:
            # If sending files, `requests` will set
            # the `Content-Type` for us.
            args.headers['Content-Type'] = TYPE_FORM

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
            params=args.queries,
        )

    except (KeyboardInterrupt, SystemExit):
        sys.stderr.write('\n')
        sys.exit(1)
    except Exception as e:
        if args.traceback:
            raise
        sys.stderr.write(str(e.message) + '\n')
        sys.exit(1)


def get_output(args, env, response):

    do_prettify = (
        args.prettify is True or
        (args.prettify == cliparse.PRETTIFY_STDOUT_TTY_ONLY
        and env.stdout_isatty)
    )

    do_output_request = (
        cliparse.OUT_REQ_HEAD in args.output_options
        or cliparse.OUT_REQ_BODY in args.output_options
    )

    do_output_response = (
        cliparse.OUT_RESP_HEAD in args.output_options
        or cliparse.OUT_RESP_BODY in args.output_options
    )

    prettifier = None
    if do_prettify:
        prettifier = OutputProcessor(
            env, pygments_style=args.style)

    buf = []

    if do_output_request:
        req = HTTPMessage.from_request(response.request).format(
            prettifier=prettifier,
            with_headers=cliparse.OUT_REQ_HEAD in args.output_options,
            with_body=cliparse.OUT_REQ_BODY in args.output_options
        )
        buf.append(req)
        buf.append('\n')
        if do_output_response:
            buf.append('\n')

    if do_output_response:
        resp = HTTPMessage.from_response(response).format(
            prettifier=prettifier,
            with_headers=cliparse.OUT_RESP_HEAD in args.output_options,
            with_body=cliparse.OUT_RESP_BODY in args.output_options
        )
        buf.append(resp)
        buf.append('\n')

    return ''.join(buf)


def get_exist_status(code, allow_redirects=False):
    """
    Translate HTTP status code to exit status.

    """
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
    """
    Run the main program and write the output to ``env.stdout``.

    Return exit status.

    """
    args = cli.parser.parse_args(args=args, env=env)
    response = get_response(args)

    status = 0

    if args.check_status:
        status = get_exist_status(response.status_code,
                                  args.allow_redirects)
        if status and not env.stdout_isatty:
            err = 'http error: %s %s\n' % (
                response.raw.status, response.raw.reason)
            env.stderr.write(err.encode('utf8'))

    output = get_output(args, env, response)
    output_bytes = output.encode('utf8')
    f = getattr(env.stdout, 'buffer', env.stdout)
    f.write(output_bytes)

    return status
