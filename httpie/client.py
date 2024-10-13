from __future__ import annotations

import argparse
import json
import sys
import typing
from pathlib import Path
from random import randint
from time import monotonic
from typing import Any, Dict, Callable, Iterable
from urllib.parse import urlparse, urlunparse

import niquests

from . import __version__
from .adapters import HTTPieHTTPAdapter
from .compat import urllib3, SKIP_HEADER, SKIPPABLE_HEADERS, parse_url, Timeout
from .cli.constants import HTTP_OPTIONS
from .cli.dicts import HTTPHeadersDict
from .cli.nested_json import unwrap_top_level_list_if_needed
from .context import Environment
from .encoding import UTF8
from .models import RequestsMessage
from .plugins.registry import plugin_manager
from .sessions import get_httpie_session
from .ssl_ import AVAILABLE_SSL_VERSION_ARG_MAPPING, HTTPieCertificate, HTTPieHTTPSAdapter, QuicCapabilityCache
from .uploads import (
    compress_request, prepare_request_body,
    get_multipart_data_and_content_type,
)
from .utils import get_expired_cookies, repr_dict


urllib3.disable_warnings()

FORM_CONTENT_TYPE = f'application/x-www-form-urlencoded; charset={UTF8}'
JSON_CONTENT_TYPE = 'application/json'
JSON_ACCEPT = f'{JSON_CONTENT_TYPE}, */*;q=0.5'
DEFAULT_UA = f'HTTPie/{__version__}'

IGNORE_CONTENT_LENGTH_METHODS = frozenset([HTTP_OPTIONS])


def collect_messages(
    env: Environment,
    args: argparse.Namespace,
    request_body_read_callback: Callable[[bytes], None] = None,
    request_or_response_callback: Callable[[niquests.PreparedRequest | niquests.Response], None] = None,
) -> Iterable[RequestsMessage]:
    httpie_session = None
    httpie_session_headers = None
    if args.session or args.session_read_only:
        httpie_session = get_httpie_session(
            env=env,
            config_dir=env.config.directory,
            session_name=args.session or args.session_read_only,
            host=args.headers.get('Host'),
            url=args.url,
        )
        httpie_session_headers = httpie_session.headers

    request_kwargs = make_request_kwargs(
        env,
        args=args,
        base_headers=httpie_session_headers,
        request_body_read_callback=request_body_read_callback
    )
    send_kwargs = make_send_kwargs(args)
    send_kwargs_mergeable_from_env = make_send_kwargs_mergeable_from_env(args)

    source_address = None

    if args.interface:
        source_address = (args.interface, 0)
    if args.local_port:
        if '-' not in args.local_port:
            source_address = (args.interface or "0.0.0.0", int(args.local_port))
        else:
            min_port, max_port = args.local_port.split('-', 1)
            source_address = (args.interface or "0.0.0.0", randint(int(min_port), int(max_port)))

    parsed_url = parse_url(args.url)
    resolver = args.resolver or None

    # we want to make sure every ".localhost" host resolve to loopback
    if parsed_url.host and parsed_url.host.endswith(".localhost"):
        ensure_resolver = f"in-memory://default/?hosts={parsed_url.host}:127.0.0.1&hosts={parsed_url.host}:[::1]"

        if resolver and isinstance(resolver, list):
            resolver.append(ensure_resolver)
        else:
            resolver = [ensure_resolver, "system://"]

    if args.force_http1:
        args.disable_http1 = False
        args.disable_http2 = True
        args.disable_http3 = True

    if args.force_http2:
        args.disable_http1 = True
        args.disable_http2 = False
        args.disable_http3 = True

    if args.force_http3:
        args.disable_http1 = True
        args.disable_http2 = True
        args.disable_http3 = False

    requests_session = build_requests_session(
        ssl_version=args.ssl_version,
        ciphers=args.ciphers,
        verify=bool(send_kwargs_mergeable_from_env['verify']),
        disable_http1=args.disable_http1,
        disable_http2=args.disable_http2,
        disable_http3=args.disable_http3,
        resolver=resolver,
        disable_ipv6=args.ipv4,
        disable_ipv4=args.ipv6,
        source_address=source_address,
        quic_cache=env.config.quic_file,
    )

    if args.disable_http3 is False and args.force_http3 is True:
        requests_session.quic_cache_layer[(parsed_url.host, parsed_url.port or 443)] = (parsed_url.host, parsed_url.port or 443)
    # well, this one is tricky. If we allow HTTP/3, and remote host was marked as QUIC capable
    # but is not anymore, we may face an indefinite hang if timeout isn't set. This could surprise some user.
    elif (
        args.disable_http3 is False
        and requests_session.quic_cache_layer.get((parsed_url.host, parsed_url.port or 443)) is not None
        and args.force_http3 is False
    ):
        # we only set the connect timeout, the rest is still indefinite.
        if send_kwargs["timeout"] is None:
            send_kwargs["timeout"] = Timeout(connect=3)
        setattr(args, "_failsafe_http3", True)

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

    hooks = None

    # The hook set up bellow is crucial for HTTPie.
    # It will help us yield the request before it is
    # actually sent. This will permit us to know about
    # the connection information for example.
    if request_or_response_callback:
        hooks = {"pre_send": [request_or_response_callback], "early_response": [request_or_response_callback]}

    request = niquests.Request(**request_kwargs, hooks=hooks)
    prepared_request = requests_session.prepare_request(request)
    transform_headers(request, prepared_request)
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
            response = requests_session.send(
                request=prepared_request,
                **send_kwargs_merged,
                **send_kwargs,
            )
            if args.max_headers and len(response.headers) > args.max_headers:
                try:
                    requests_session.close()
                    # we consume the content to allow the connection to be put back into the pool, and closed!
                    response.content
                except NotImplementedError:  # We allow custom transports that may not implement close.
                    pass

                raise niquests.ConnectionError(f"got more than {args.max_headers} headers")
            response._httpie_headers_parsed_at = monotonic()
            expired_cookies += get_expired_cookies(
                response.headers.get('Set-Cookie', '')
            )

            response_count += 1
            if response.next:
                if args.max_redirects and response_count == args.max_redirects:
                    raise niquests.TooManyRedirects
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
            httpie_session.remove_cookies(expired_cookies)
            httpie_session.save()

    try:
        requests_session.close()
    except NotImplementedError:  # We allow custom transports that may not implement close.
        pass


def build_requests_session(
    verify: bool,
    ssl_version: str = None,
    ciphers: str = None,
    disable_http1: bool = False,
    disable_http2: bool = False,
    disable_http3: bool = False,
    resolver: typing.List[str] = None,
    disable_ipv4: bool = False,
    disable_ipv6: bool = False,
    source_address: typing.Tuple[str, int] = None,
    quic_cache: typing.Optional[Path] = None,
) -> niquests.Session:
    requests_session = niquests.Session()

    if quic_cache is not None:
        requests_session.quic_cache_layer = QuicCapabilityCache(quic_cache)

    if resolver:
        resolver_rebuilt = []
        for r in resolver:
            # assume it is the in-memory resolver
            if "://" not in r:
                r = f"in-memory://default/?hosts={r}"
            resolver_rebuilt.append(r)
        resolver = resolver_rebuilt

    # Install our adapter.
    http_adapter = HTTPieHTTPAdapter(
        resolver=resolver,
        disable_ipv4=disable_ipv4,
        disable_ipv6=disable_ipv6,
        source_address=source_address,
        disable_http1=disable_http1,
        disable_http2=disable_http2,
    )
    https_adapter = HTTPieHTTPSAdapter(
        ciphers=ciphers,
        verify=verify,
        ssl_version=(
            AVAILABLE_SSL_VERSION_ARG_MAPPING[ssl_version]
            if ssl_version else None
        ),
        disable_http1=disable_http1,
        disable_http2=disable_http2,
        disable_http3=disable_http3,
        resolver=resolver,
        disable_ipv4=disable_ipv4,
        disable_ipv6=disable_ipv6,
        source_address=source_address,
        quic_cache_layer=requests_session.quic_cache_layer,
    )
    requests_session.mount('http://', http_adapter)
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
        f'\n>>> niquests.request(**{repr_dict(kwargs)})\n\n')


def finalize_headers(headers: HTTPHeadersDict) -> HTTPHeadersDict:
    final_headers = HTTPHeadersDict()
    for name, value in headers.items():
        if value is not None:
            # “leading or trailing LWS MAY be removed without
            # changing the semantics of the field value”
            # <https://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html>
            # Also, requests raises `InvalidHeader` for leading spaces.
            value = value.strip()
            if isinstance(value, str):
                # See <https://github.com/httpie/cli/issues/212>
                value = value.encode()
        elif name.lower() in SKIPPABLE_HEADERS:
            # Some headers get overwritten by urllib3 when set to `None`
            # and should be replaced with the `SKIP_HEADER` constant.
            value = SKIP_HEADER
        final_headers.add(name, value)
    return final_headers


def transform_headers(
    request: niquests.Request,
    prepared_request: niquests.PreparedRequest
) -> None:
    """Apply various transformations on top of the `prepared_requests`'s
    headers to change the request prepreation behavior."""

    # Remove 'Content-Length' when it is misplaced by niquests.
    if (
        prepared_request.method in IGNORE_CONTENT_LENGTH_METHODS
        and prepared_request.headers.get('Content-Length') == '0'
        and request.headers.get('Content-Length') != '0'
    ):
        prepared_request.headers.pop('Content-Length')

    apply_missing_repeated_headers(
        request.headers,
        prepared_request
    )


def apply_missing_repeated_headers(
    original_headers: HTTPHeadersDict,
    prepared_request: niquests.PreparedRequest
) -> None:
    """Update the given `prepared_request`'s headers with the original
    ones. This allows the requests to be prepared as usual, and then later
    merged with headers that are specified multiple times."""

    new_headers = HTTPHeadersDict(prepared_request.headers)
    for prepared_name, prepared_value in prepared_request.headers.items():
        if prepared_name not in original_headers:
            continue

        original_keys, original_values = zip(*filter(
            lambda item: item[0].casefold() == prepared_name.casefold(),
            original_headers.items()
        ))

        if prepared_value not in original_values:
            # If the current value is not among the initial values
            # set for this field, then it means that this field got
            # overridden on the way, and we should preserve it.
            continue

        new_headers.popone(prepared_name)
        new_headers.update(zip(original_keys, original_values))

    prepared_request.headers = new_headers


def make_default_headers(args: argparse.Namespace) -> HTTPHeadersDict:
    default_headers = HTTPHeadersDict({
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
    return {
        'timeout': args.timeout or None,
        'allow_redirects': False,
    }


def make_send_kwargs_mergeable_from_env(args: argparse.Namespace) -> dict:
    cert = None
    if args.cert:
        cert = args.cert
        if args.cert_key:
            cert = HTTPieCertificate(cert, args.cert_key, args.cert_key_pass.value)

    return {
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


def json_dict_to_request_body(data: Dict[str, Any]) -> str:
    data = unwrap_top_level_list_if_needed(data)
    if data:
        data = json.dumps(data)
    else:
        # We need to set data to an empty string to prevent requests
        # from assigning an empty list to `response.request.data`.
        data = ''
    return data


def make_request_kwargs(
    env: Environment,
    args: argparse.Namespace,
    base_headers: HTTPHeadersDict = None,
    request_body_read_callback=lambda chunk: chunk
) -> dict:
    """
    Translate our `args` into `niquests.Request` keyword arguments.

    """
    files = args.files
    # Serialize JSON data, if needed.
    data = args.data
    auto_json = data and not args.form
    if (args.json or auto_json) and isinstance(data, dict):
        data = json_dict_to_request_body(data)

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

    return {
        'method': args.method.lower(),
        'url': args.url,
        'headers': headers,
        'data': prepare_request_body(
            env,
            data,
            body_read_callback=request_body_read_callback,
            chunked=args.chunked,
            offline=args.offline,
            content_length_header_value=headers.get('Content-Length'),
        ),
        'auth': args.auth,
        'params': args.params.items(),
    }


def ensure_path_as_is(orig_url: str, prepped_url: str) -> str:
    """
    Handle `--path-as-is` by replacing the path component of the prepared
    URL with the path component from the original URL. Other parts stay
    untouched because other (welcome) processing on the URL might have
    taken place.

    <https://github.com/httpie/cli/issues/895>


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
    return urlunparse(tuple(final_dict.values()))
