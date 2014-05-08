import json
import sys
from pprint import pformat

import requests

from . import sessions
from . import __version__
from .compat import str
from .plugins import plugin_manager


FORM = 'application/x-www-form-urlencoded; charset=utf-8'
JSON = 'application/json; charset=utf-8'
DEFAULT_UA = 'HTTPie/%s' % __version__


def get_response(args, config_dir):
    """Send the request and return a `request.Response`."""

    if not args.session and not args.session_read_only:
        requests_kwargs = get_requests_kwargs(args)
        if args.debug:
            dump_request(requests_kwargs)
        response = requests.request(**requests_kwargs)
    else:
        response = sessions.get_response(
            args=args,
            config_dir=config_dir,
            session_name=args.session or args.session_read_only,
            read_only=bool(args.session_read_only),
        )

    return response


def dump_request(kwargs):
    sys.stderr.write('\n>>> requests.request(%s)\n\n'
                     % pformat(kwargs))


def encode_headers(headers):
    # This allows for unicode headers which is non-standard but practical.
    # See: https://github.com/jakubroztocil/httpie/issues/212
    return dict(
        (name, value.encode('utf8') if isinstance(value, str) else value)
        for name, value in headers.items()
    )


def get_default_headers(args):
    default_headers = {
        'User-Agent': DEFAULT_UA
    }

    auto_json = args.data and not args.form
    # FIXME: Accept is set to JSON with `http url @./file.txt`.
    if args.json or auto_json:
        default_headers['Accept'] = 'application/json'
        if args.json or (auto_json and args.data):
            default_headers['Content-Type'] = JSON

    elif args.form and not args.files:
        # If sending files, `requests` will set
        # the `Content-Type` for us.
        default_headers['Content-Type'] = FORM
    return default_headers


def get_requests_kwargs(args, base_headers=None):
    """
    Translate our `args` into `requests.request` keyword arguments.

    """
    # Serialize JSON data, if needed.
    data = args.data
    auto_json = data and not args.form
    if args.json or auto_json and isinstance(data, dict):
        if data:
            data = json.dumps(data)
        else:
            # We need to set data to an empty string to prevent requests
            # from assigning an empty list to `response.request.data`.
            data = ''

    # Finalize headers.
    headers = get_default_headers(args)
    if base_headers:
        headers.update(base_headers)
    headers.update(args.headers)
    headers = encode_headers(headers)

    credentials = None
    if args.auth:
        auth_plugin = plugin_manager.get_auth_plugin(args.auth_type)()
        credentials = auth_plugin.get_auth(args.auth.key, args.auth.value)

    cert = None
    if args.cert:
        cert = args.cert
        if args.certkey:
            cert = cert, args.certkey

    kwargs = {
        'stream': True,
        'method': args.method.lower(),
        'url': args.url,
        'headers': headers,
        'data': data,
        'verify': {
            'yes': True,
            'no': False
        }.get(args.verify, args.verify),
        'cert': cert,
        'timeout': args.timeout,
        'auth': credentials,
        'proxies': dict((p.key, p.value) for p in args.proxy),
        'files': args.files,
        'allow_redirects': args.follow,
        'params': args.params,
    }

    return kwargs
