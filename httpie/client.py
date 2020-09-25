import argparse
import http.client
import json
import sys
import zlib
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Union
from urllib.parse import urlparse, urlunparse

import httpx
# noinspection PyPackageRequirements
from httpie import __version__
from httpie.plugins.registry import plugin_manager
from httpie.sessions import get_httpie_session
from httpie.ssl import AVAILABLE_SSL_VERSION_ARG_MAPPING, HTTPieHTTPSAdapter
from httpie.uploads import get_multipart_data_and_content_type
from httpie.utils import get_expired_cookies, repr_dict


FORM_CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=utf-8'
JSON_CONTENT_TYPE = 'application/json'
JSON_ACCEPT = f'{JSON_CONTENT_TYPE}, */*;q=0.5'
DEFAULT_UA = f'HTTPie/{__version__}'


def collect_messages(
    args: argparse.Namespace,
    config_dir: Path,
) -> Iterable[Union[httpx.Request, httpx.Response]]:
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
    httpx_session = build_httpx_session(
        ssl_version=args.ssl_version,
        ciphers=args.ciphers,
        verify=bool(send_kwargs_mergeable_from_env['verify'])
    )

    if httpie_session:
        httpie_session.update_headers(request_kwargs['headers'])
        httpx_session.cookies = httpie_session.cookies
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

    request = httpx_session.build_request(**request_kwargs)
    if args.path_as_is:
        request.url = ensure_path_as_is(
            orig_url=args.url,
            prepped_url=request.url,
        )
    request.read()
    if args.compress and request.content:
        request = compress_body(request, always=args.compress > 1)
    response_count = 0
    expired_cookies = []
    while request:
        yield request
        if not args.offline:
            with max_headers(args.max_headers):
                assert not isinstance(request, httpx.Response)
                response = httpx_session.send(
                    request=request,
                    **send_kwargs,
                )

            # noinspection PyProtectedMember
            # expired_cookies += get_expired_cookies(
            #     headers=response.raw._original_response.msg._headers
            # )

            response_count += 1
            if response.is_redirect:
                if args.max_redirects and response_count == args.max_redirects:
                    raise httpx.TooManyRedirects
                if args.follow:
                    request = response.next()
                    if args.all:
                        yield response
                    continue
            yield response
        break

    if httpie_session:
        if httpie_session.is_new() or not args.session_read_only:
            httpie_session.cookies = httpx_session.cookies
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


def compress_body(request: httpx.Request, always: bool) -> httpx.Request:
    deflater = zlib.compressobj()
    deflated_data = deflater.compress(request.content)
    deflated_data += deflater.flush()
    is_economical = len(deflated_data) < len(request.content)
    if is_economical or always:
        request = httpx.Request(method=request.method, url=request.url, headers=request.headers, content=deflated_data)
        request.headers['Content-Encoding'] = 'deflate'
        request.headers['Content-Length'] = str(len(deflated_data))
    return request

def build_httpx_session(
    verify: bool,
    ssl_version: str = None,
    ciphers: str = None,
) -> httpx.Client:
    httpx_session = httpx.Client()

    # # Install our adapter.
    # https_adapter = HTTPieHTTPSAdapter(
    #     ciphers=ciphers,
    #     verify=verify,
    #     ssl_version=(
    #         AVAILABLE_SSL_VERSION_ARG_MAPPING[ssl_version]
    #         if ssl_version else None
    #     ),
    # )
    # httpx_session.mount('https://', https_adapter)
    #
    # # Install adapters from plugins.
    # for plugin_cls in plugin_manager.get_transport_plugins():
    #     transport_plugin = plugin_cls()
    #     httpx_session.mount(
    #         prefix=transport_plugin.prefix,
    #         adapter=transport_plugin.get_adapter(),
    #     )

    return httpx_session


def dump_request(kwargs: dict):
    sys.stderr.write(
        f'\n>>> httpx.request(**{repr_dict(kwargs)})\n\n')


def finalize_headers(headers: httpx.Headers) -> httpx.Headers:
    final_headers = httpx.Headers()
    for name, value in headers.items():
        if value is not None:
            # “leading or trailing LWS MAY be removed without
            # changing the semantics of the field value”
            # <https://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html>
            # Also, requests raises `InvalidHeader` for leading spaces.
            value = value.strip()
        final_headers[name] = value
    return final_headers


def make_default_headers(args: argparse.Namespace) -> httpx.Headers:
    default_headers = httpx.Headers({
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
        'auth': args.auth,
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
    base_headers: httpx.Headers = None
) -> dict:
    """
    Translate our `args` into `httpx.Request` keyword arguments.

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
    headers = finalize_headers(headers)

    if args.form and (files or args.multipart):
        pass
        # data, headers['Content-Type'] = get_multipart_data_and_content_type(
        #     data=data,
        #     files=files,
        #     boundary=args.boundary,
        #     content_type=args.headers.get('Content-Type'),
        # )
        # files = None

    kwargs = {
        'method': args.method.lower(),
        'url': args.url,
        'headers': headers,
        'data': data,
        'params': args.params,
        'files': files,
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
