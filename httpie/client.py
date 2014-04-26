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

    requests_kwargs = get_requests_kwargs(args)

    if args.debug:
        sys.stderr.write('\n>>> requests.request(%s)\n\n'
                         % pformat(requests_kwargs))

    if not args.session and not args.session_read_only:
        response = requests.request(**requests_kwargs)
    else:
        response = sessions.get_response(
            args=args,
            config_dir=config_dir,
            session_name=args.session or args.session_read_only,
            requests_kwargs=requests_kwargs,
            read_only=bool(args.session_read_only),
        )

    return response


def encode_headers(headers):
    # This allows for unicode headers which is non-standard but practical.
    # See: https://github.com/jkbr/httpie/issues/212
    return dict(
        (name, value.encode('utf8') if isinstance(value, str) else value)
        for name, value in headers.items()
    )


def get_requests_kwargs(args):
    """Translate our `args` into `requests.request` keyword arguments."""

    implicit_headers = {
        'User-Agent': DEFAULT_UA
    }

    auto_json = args.data and not args.form
    # FIXME: Accept is set to JSON with `http url @./file.txt`.
    if args.json or auto_json:
        implicit_headers['Accept'] = 'application/json'
        if args.json or (auto_json and args.data):
            implicit_headers['Content-Type'] = JSON

        if isinstance(args.data, dict):
            if args.data:
                args.data = json.dumps(args.data)
            else:
                # We need to set data to an empty string to prevent requests
                # from assigning an empty list to `response.request.data`.
                args.data = ''

    elif args.form and not args.files:
        # If sending files, `requests` will set
        # the `Content-Type` for us.
        implicit_headers['Content-Type'] = FORM

    for name, value in implicit_headers.items():
        if name not in args.headers:
            args.headers[name] = value

    credentials = None
    if args.auth:
        auth_plugin = plugin_manager.get_auth_plugin(args.auth_type)()
        credentials = auth_plugin.get_auth(args.auth.key, args.auth.value)

    cert = None
    if args.cert:
        cert = args.cert
        if args.certkey:
            cert = (cert, args.certkey)

    kwargs = {
        'stream': True,
        'method': args.method.lower(),
        'url': args.url,
        'headers': encode_headers(args.headers),
        'data': args.data,
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
