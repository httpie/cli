import argparse
import http.client
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterable, Union
from urllib.parse import urlparse, urlunparse

import requests
# noinspection PyPackageRequirements
import urllib3
from httpie import __version__
from httpie.cli.dicts import RequestHeadersDict
from httpie.plugins.registry import plugin_manager
from httpie.sessions import get_httpie_session
from httpie.ssl import AVAILABLE_SSL_VERSION_ARG_MAPPING, HTTPieHTTPSAdapter
from httpie.uploads import (
    compress_request, prepare_request_body,
    get_multipart_data_and_content_type,
)
from httpie.utils import get_expired_cookies, repr_dict


urllib3.disable_warnings()

FORM_CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=utf-8'
JSON_CONTENT_TYPE = 'application/json'
JSON_ACCEPT = f'{JSON_CONTENT_TYPE}, */*;q=0.5'
DEFAULT_UA = f'HTTPie/{__version__}'


def collect_messages(
    args: argparse.Namespace,
    config_dir: Path,
    request_body_read_callback: Callable[[bytes], None] = None,
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
        request_body_read_callback=request_body_read_callback
    )
    send_kwargs = make_send_kwargs(args)
    send_kwargs_mergeable_from_env = make_send_kwargs_mergeable_from_env(args)
    requests_session = build_requests_session(
        ssl_version=args.ssl_version,
        ciphers=args.ciphers,
        verify=bool(send_kwargs_mergeable_from_env['verify'])
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
    if args.path_as_is:
        prepared_request.url = ensure_path_as_is(
            orig_url=args.url,
            prepped_url=prepared_request.url,
        )
    if args.compress and prepared_request.body:
        compress_request(
            request=prepared_request,
            always=args.compress > 1,
        )
    response_count = 0
    expired_cookies = []
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

            # noinspection PyProtectedMember
            expired_cookies += get_expired_cookies(
                headers=response.raw._original_response.msg._headers
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
            httpie_session.remove_cookies(
                # TODO: take path & domain into account?
                cookie['name'] for cookie in expired_cookies
            )
            httpie_session.save()


# noinspection PyProtectedMember
@contextmanager
def max_headers(limit):
    # <https://github.com/jakubroztocil/httpie/issues/802>
    # noinspection PyUnresolvedReferences
    orig = http.client._MAXHEADERS
    http.client._MAXHEADERS = limit or float('Inf')
    try:
        yield
    finally:
        http.client._MAXHEADERS = orig


def build_requests_session(
    verify: bool,
    ssl_version: str = None,
    ciphers: str = None,
) -> requests.Session:
    requests_session = requests.Session()

    # Install our adapter.
    https_adapter = HTTPieHTTPSAdapter(
        ciphers=ciphers,
        verify=verify,
        ssl_version=(
            AVAILABLE_SSL_VERSION_ARG_MAPPING[ssl_version]
            if ssl_version else None
        ),
    )
    requests_session.mount('https://', https_adapter)

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
    base_headers: RequestHeadersDict = None,
    request_body_read_callback=lambda chunk: chunk
) -> dict:
    """
    Translate our `args` into `requests.Request` keyword arguments.

    """
    files = args.files
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
    if args.offline and args.chunked and 'Transfer-Encoding' not in headers:
        # When online, we let requests set the header instead to be able more
        # easily verify chunking is taking place.
        headers['Transfer-Encoding'] = 'chunked'
    headers = finalize_headers(headers)

    if (args.form and files) or args.multipart:
        data, headers['Content-Type'] = get_multipart_data_and_content_type(
            data=args.multipart_data,
            boundary=args.boundary,
            content_type=args.headers.get('Content-Type'),
        )

    kwargs = {
        'method': args.method.lower(),
        'url': args.url,
        'headers': headers,
        'data': prepare_request_body(
            body=data,
            body_read_callback=request_body_read_callback,
            chunked=args.chunked,
            offline=args.offline,
            content_length_header_value=headers.get('Content-Length'),
        ),
        'auth': args.auth,
        'params': args.params.items(),
    }

    return kwargs


def ensure_path_as_is(orig_url: str, prepped_url: str) -> str:
    """
    Handle `--path-as-is` by replacing the path component of the prepared
    URL with the path component from the original URL. Other parts stay
    untouched because other (welcome) processing on the URL might have
    taken place.

    <https://github.com/jakubroztocil/httpie/issues/895>


    <https://ec.haxx.se/http/http-basics#path-as-is>
    <https://curl.haxx.se/libcurl/c/CURLOPT_PATH_AS_IS.html>

    >>> ensure_path_as_is('http://foo/../', 'http://foo/?foo=bar')
    'http://foo/../?foo=bar'

    """
    parsed_orig, parsed_prepped = urlparse(orig_url), urlparse(prepped_url)
    final_dict = {
        # noinspection PyProtectedMember
        **parsed_prepped._asdict(),
        'path': parsed_orig.path,
    }
    final_url = urlunparse(tuple(final_dict.values()))
    return final_url
