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
    # noinspection PyPackageRequirements
    import urllib3
    # <https://urllib3.readthedocs.io/en/latest/security.html>
    urllib3.disable_warnings()
except (ImportError, AttributeError):
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

    def __init__(
        self,
        ssl_version=None,
        compression_enabled=False,
        compress_always=False,
        **kwargs,
    ):
        self._ssl_version = ssl_version
        self._compression_enabled = compression_enabled
        self._compress_always = compress_always
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_version'] = self._ssl_version
        super().init_poolmanager(*args, **kwargs)

    def send(self, request: requests.PreparedRequest, **kwargs):
        if request.body and self._compression_enabled:
            self._compress_body(request, always=self._compress_always)
        return super().send(request, **kwargs)

    @staticmethod
    def _compress_body(request: requests.PreparedRequest, always: bool):
        deflater = zlib.compressobj()
        body_bytes = (
            request.body
            if isinstance(request.body, bytes)
            else request.body.encode()
        )
        deflated_data = deflater.compress(body_bytes)
        deflated_data += deflater.flush()
        is_economical = len(deflated_data) < len(body_bytes)
        if is_economical or always:
            request.body = deflated_data
            request.headers['Content-Encoding'] = 'deflate'
            request.headers['Content-Length'] = str(len(deflated_data))


def build_requests_session(
    ssl_version: str,
    compress_arg: int,
) -> requests.Session:
    requests_session = requests.Session()

    # Install our adapter.
    adapter = HTTPieHTTPAdapter(
        ssl_version=ssl_version,
        compression_enabled=compress_arg > 0,
        compress_always=compress_arg > 1,
    )
    requests_session.mount('http://', adapter)
    requests_session.mount('https://', adapter)

    # Install adapters from plugins.
    for plugin_cls in plugin_manager.get_transport_plugins():
        transport_plugin = plugin_cls()
        requests_session.mount(
            prefix=transport_plugin.prefix,
            adapter=transport_plugin.get_adapter(),
        )

    return requests_session


def get_response(
    args: argparse.Namespace,
    config_dir: Path
) -> requests.Response:
    """Send the request and return a `request.Response`."""

    ssl_version = None
    if args.ssl_version:
        ssl_version = SSL_VERSION_ARG_MAPPING[args.ssl_version]

    requests_session = build_requests_session(
        ssl_version=ssl_version,
        compress_arg=args.compress
    )
    requests_session.max_redirects = args.max_redirects

    with max_headers(args.max_headers):
        if not args.session and not args.session_read_only:
            kwargs = make_requests_kwargs(args)
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


def make_default_headers(args: argparse.Namespace) -> RequestHeadersDict:
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


def make_requests_kwargs(args: argparse.Namespace, base_headers=None) -> dict:
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
    headers = make_default_headers(args)
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
