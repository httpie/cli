import argparse
import http.client
import json
import sys
import zlib
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Union

import requests
from requests.adapters import HTTPAdapter

from httpie import __version__
from httpie.cli.constants import SSL_VERSION_ARG_MAPPING
from httpie.cli.dicts import RequestHeadersDict
from httpie.plugins import plugin_manager
from httpie.sessions import get_httpie_session
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


def collect_messages(
    args: argparse.Namespace,
    config_dir: Path,
) -> Iterable[Union[requests.PreparedRequest, requests.Response]]:
    httpie_session = None
    httpie_session_headers = None
    if args.session or args.session_read_only:
        httpie_session = get_httpie_session(
            config_dir=config_dir,
            session_name=args.session or args.session_read_only,
            host=args.headers.get('Host'),
            url=args.url,
        )
        httpie_session_headers = httpie_session.headers

    request_kwargs = make_request_kwargs(
        args=args,
        base_headers=httpie_session_headers,
    )
    send_kwargs = make_send_kwargs(args)
    send_kwargs_mergeable_from_env = make_send_kwargs_mergeable_from_env(args)
    requests_session = build_requests_session(
        ssl_version=args.ssl_version,
    )

    if httpie_session:
        httpie_session.update_headers(request_kwargs['headers'])
        requests_session.cookies = httpie_session.cookies
        if args.auth_plugin:
            # Save auth from CLI to HTTPie session.
            httpie_session.auth = {
                'type': args.auth_plugin.auth_type,
                'raw_auth': args.auth_plugin.raw_auth,
            }
        elif httpie_session.auth:
            # Apply auth from HTTPie session
            request_kwargs['auth'] = httpie_session.auth

    if args.debug:
        # TODO: reflect the split between request and send kwargs.
        dump_request(request_kwargs)

    request = requests.Request(**request_kwargs)
    prepared_request = requests_session.prepare_request(request)
    if args.compress and prepared_request.body:
        compress_body(prepared_request, always=args.compress > 1)
    response_count = 0
    while prepared_request:
        yield prepared_request
        if not args.offline:
            send_kwargs_merged = requests_session.merge_environment_settings(
                url=prepared_request.url,
                **send_kwargs_mergeable_from_env,
            )
            with max_headers(args.max_headers):
                response = requests_session.send(
                    request=prepared_request,
                    **send_kwargs_merged,
                    **send_kwargs,
                )
            response_count += 1
            if response.next:
                if args.max_redirects and response_count == args.max_redirects:
                    raise requests.TooManyRedirects
                if args.follow:
                    prepared_request = response.next
                    if args.all:
                        yield response
                    continue
            yield response
        break

    if httpie_session:
        if httpie_session.is_new() or not args.session_read_only:
            httpie_session.cookies = requests_session.cookies
            httpie_session.save()


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


def compress_body(request: requests.PreparedRequest, always: bool):
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


class HTTPieHTTPSAdapter(HTTPAdapter):

    def __init__(self, ssl_version=None, **kwargs):
        self._ssl_version = ssl_version
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_version'] = self._ssl_version
        super().init_poolmanager(*args, **kwargs)


def build_requests_session(
    ssl_version: str = None,
) -> requests.Session:
    requests_session = requests.Session()

    # Install our adapter.
    requests_session.mount('https://', HTTPieHTTPSAdapter(
        ssl_version=(
            SSL_VERSION_ARG_MAPPING[ssl_version]
            if ssl_version else None
        )
    ))

    # Install adapters from plugins.
    for plugin_cls in plugin_manager.get_transport_plugins():
        transport_plugin = plugin_cls()
        requests_session.mount(
            prefix=transport_plugin.prefix,
            adapter=transport_plugin.get_adapter(),
        )

    return requests_session


def dump_request(kwargs: dict):
    sys.stderr.write(
        f'\n>>> requests.request(**{repr_dict(kwargs)})\n\n')


def finalize_headers(headers: RequestHeadersDict) -> RequestHeadersDict:
    final_headers = RequestHeadersDict()
    for name, value in headers.items():
        if value is not None:
            # “leading or trailing LWS MAY be removed without
            # changing the semantics of the field value”
            # <https://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html>
            # Also, requests raises `InvalidHeader` for leading spaces.
            value = value.strip()
            if isinstance(value, str):
                # See <https://github.com/jakubroztocil/httpie/issues/212>
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


def make_send_kwargs(args: argparse.Namespace) -> dict:
    kwargs = {
        'timeout': args.timeout or None,
        'allow_redirects': False,
    }
    return kwargs


def make_send_kwargs_mergeable_from_env(args: argparse.Namespace) -> dict:
    cert = None
    if args.cert:
        cert = args.cert
        if args.cert_key:
            cert = cert, args.cert_key
    kwargs = {
        'proxies': {p.key: p.value for p in args.proxy},
        'stream': True,
        'verify': {
            'yes': True,
            'true': True,
            'no': False,
            'false': False,
        }.get(args.verify.lower(), args.verify),
        'cert': cert,
    }
    return kwargs


def make_request_kwargs(
    args: argparse.Namespace,
    base_headers: RequestHeadersDict = None
) -> dict:
    """
    Translate our `args` into `requests.Request` keyword arguments.

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

    kwargs = {
        'method': args.method.lower(),
        'url': args.url,
        'headers': headers,
        'data': data,
        'auth': args.auth,
        'params': args.params,
        'files': args.files,
    }

    return kwargs
