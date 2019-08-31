import argparse
import http.client
import json
import sys
import zlib
from contextlib import contextmanager
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

from httpie import __version__, sessions
from httpie.cli.constants import SSL_VERSION_ARG_MAPPING
from httpie.cli.dicts import RequestHeadersDict
from httpie.plugins import plugin_manager
from httpie.utils import repr_dict


try:
    # https://urllib3.readthedocs.io/en/latest/security.html
    # noinspection PyPackageRequirements
    import urllib3
    urllib3.disable_warnings()
except (ImportError, AttributeError):
    # In some rare cases, the user may have an old version of the requests
    # or urllib3, and there is no method called "disable_warnings." In these
    # cases, we don't need to call the method.
    # They may get some noisy output but execution shouldn't die. Move on.
    pass


FORM_CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=utf-8'
JSON_CONTENT_TYPE = 'application/json'
JSON_ACCEPT = f'{JSON_CONTENT_TYPE}, */*'
DEFAULT_UA = f'HTTPie/{__version__}'


# noinspection PyProtectedMember
@contextmanager
def max_headers(limit):
    # <https://github.com/jakubroztocil/httpie/issues/802>
    orig = http.client._MAXHEADERS
    http.client._MAXHEADERS = limit or float('Inf')
    try:
        yield
    finally:
        http.client._MAXHEADERS = orig


class HTTPieHTTPAdapter(HTTPAdapter):

    def __init__(self, ssl_version=None, compress=0, **kwargs):
        self._ssl_version = ssl_version
        self._compress = compress
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_version'] = self._ssl_version
        super().init_poolmanager(*args, **kwargs)

    def send(self, request: requests.PreparedRequest, **kwargs):
        if self._compress and request.body:
            self._compress_body(request, self._compress)
        return super().send(request, **kwargs)

    @staticmethod
    def _compress_body(request: requests.PreparedRequest, compress: int):
        deflater = zlib.compressobj()
        if isinstance(request.body, bytes):
            deflated_data = deflater.compress(request.body)
        else:
            deflated_data = deflater.compress(request.body.encode())
        deflated_data += deflater.flush()
        if len(deflated_data) < len(request.body) or compress > 1:
            request.body = deflated_data
            request.headers['Content-Encoding'] = 'deflate'
            request.headers['Content-Length'] = str(len(deflated_data))


def get_requests_session(ssl_version: str, compress: int) -> requests.Session:
    requests_session = requests.Session()
    adapter = HTTPieHTTPAdapter(ssl_version=ssl_version, compress=compress)
    for prefix in ['http://', 'https://']:
        requests_session.mount(prefix, adapter)

    for cls in plugin_manager.get_transport_plugins():
        transport_plugin = cls()
        requests_session.mount(prefix=transport_plugin.prefix,
                               adapter=transport_plugin.get_adapter())
    return requests_session


def get_response(
    args: argparse.Namespace,
    config_dir: Path
) -> requests.Response:
    """Send the request and return a `request.Response`."""

    ssl_version = None
    if args.ssl_version:
        ssl_version = SSL_VERSION_ARG_MAPPING[args.ssl_version]

    requests_session = get_requests_session(ssl_version, args.compress)
    requests_session.max_redirects = args.max_redirects

    with max_headers(args.max_headers):
        if not args.session and not args.session_read_only:
            kwargs = get_requests_kwargs(args)
            if args.debug:
                dump_request(kwargs)
            response = requests_session.request(**kwargs)
        else:
            response = sessions.get_response(
                requests_session=requests_session,
                args=args,
                config_dir=config_dir,
                session_name=args.session or args.session_read_only,
                read_only=bool(args.session_read_only),
            )

    return response


def dump_request(kwargs: dict):
    sys.stderr.write(
        f'\n>>> requests.request(**{repr_dict(kwargs)})\n\n')


def finalize_headers(headers: RequestHeadersDict) -> RequestHeadersDict:
    final_headers = RequestHeadersDict()
    for name, value in headers.items():
        if value is not None:
            # >leading or trailing LWS MAY be removed without
            # >changing the semantics of the field value"
            # -https://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html
            # Also, requests raises `InvalidHeader` for leading spaces.
            value = value.strip()
            if isinstance(value, str):
                # See: https://github.com/jakubroztocil/httpie/issues/212
                value = value.encode('utf8')
        final_headers[name] = value
    return final_headers


def get_default_headers(args: argparse.Namespace) -> RequestHeadersDict:
    default_headers = RequestHeadersDict({
        'User-Agent': DEFAULT_UA
    })

    auto_json = args.data and not args.form
    if args.json or auto_json:
        default_headers['Accept'] = JSON_ACCEPT
        if args.json or (auto_json and args.data):
            default_headers['Content-Type'] = JSON_CONTENT_TYPE

    elif args.form and not args.files:
        # If sending files, `requests` will set
        # the `Content-Type` for us.
        default_headers['Content-Type'] = FORM_CONTENT_TYPE
    return default_headers


def get_requests_kwargs(args: argparse.Namespace, base_headers=None) -> dict:
    """
    Translate our `args` into `requests.request` keyword arguments.

    """
    # Serialize JSON data, if needed.
    data = args.data
    auto_json = data and not args.form
    if (args.json or auto_json) and isinstance(data, dict):
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
    headers = finalize_headers(headers)

    cert = None
    if args.cert:
        cert = args.cert
        if args.cert_key:
            cert = cert, args.cert_key

    kwargs = {
        'stream': True,
        'method': args.method.lower(),
        'url': args.url,
        'headers': headers,
        'data': data,
        'verify': {
            'yes': True,
            'true': True,
            'no': False,
            'false': False,
        }.get(args.verify.lower(), args.verify),
        'cert': cert,
        'timeout': args.timeout or None,
        'auth': args.auth,
        'proxies': {p.key: p.value for p in args.proxy},
        'files': args.files,
        'allow_redirects': args.follow,
        'params': args.params,
    }

    return kwargs
