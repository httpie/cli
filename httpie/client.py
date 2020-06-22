import argparse
import http.client
import json
import sys
import zlib
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Union, Tuple
from urllib.parse import urlparse, urlunparse

import requests
# noinspection PyPackageRequirements
import urllib3

from httpie import __version__
from httpie.cli.dicts import RequestHeadersDict
from httpie.plugins.registry import plugin_manager
from httpie.sessions import get_httpie_session, Session
from httpie.ssl import AVAILABLE_SSL_VERSION_ARG_MAPPING, HTTPieHTTPSAdapter
from httpie.utils import get_expired_cookies, repr_dict

urllib3.disable_warnings()

FORM_CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=utf-8'
JSON_CONTENT_TYPE = 'application/json'
JSON_ACCEPT = f'{JSON_CONTENT_TYPE}, */*;q=0.5'
DEFAULT_UA = f'HTTPie/{__version__}'


def make_send_kwargs(args: argparse.Namespace) -> dict:
    cert = None
    if args.cert:
        cert = args.cert
        if args.cert_key:
            cert = args.cert, args.cert_key

    return {
        'timeout': args.timeout or None,
        'allow_redirects': False,
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


def prepare_sessions(
    args: argparse.Namespace,
    config_dir: Path,
) -> Tuple[dict, dict, Session, requests.Session]:
    """Loads or creates HTTPie Session object
    Overrides session file configurations with command line args
    Prepares keyword arguments
    Creates a requests RequestSession object

    Args:
        args (argparse.Namespace): Command line arguments
        config_dir (Path): Path to find or create Session file

    Returns:
        Tuple[dict, dict, Session, requests.Session]: Keyword arguments and Session objects
    """

    httpie_session = get_httpie_session(
        config_dir=config_dir,
        session_name=args.session or args.session_read_only,
        host=args.headers.get('Host'),
        url=args.url,
    )

    httpie_session_headers = None
    if httpie_session:
        httpie_session_headers = httpie_session.headers

    request_kwargs = make_request_kwargs(
        args=args,
        base_headers=httpie_session_headers,
    )

    send_kwargs = make_send_kwargs(args)

    requests_session = build_requests_session(
        ssl_version=args.ssl_version,
        ciphers=args.ciphers,
        verify=bool(send_kwargs['verify'])
    )

    if httpie_session:
        httpie_session.update_auth(args.auth_plugin)
        if httpie_session.auth:
            # Apply auth from HTTPie session
            request_kwargs['auth'] = httpie_session.auth
        httpie_session.update_headers(request_kwargs['headers'])
        requests_session.cookies = httpie_session.cookies

    return request_kwargs, send_kwargs, httpie_session, requests_session


def create_prepared_request(
    args: argparse.Namespace,
    requests_session: requests.Session,
    request_kwargs: dict
) -> requests.PreparedRequest:
    """Creates a PreparedRequest object
    Leaves relative path as input if `path_as_is` specified in args
    Compresses request body if `compress` specified in args

    Args:
        args (argparse.Namespace): Command line arguments
        requests_session (requests.Session): Preprepared requests.Session object
        request_kwargs (dict): Prepared keyword arguments for request

    Returns:
        requests.PreparedRequest: Created PreparedRequest object
    """

    request = requests.Request(**request_kwargs)
    prepared_request = requests_session.prepare_request(request)

    if args.path_as_is:
        prepared_request.url = ensure_path_as_is(
            orig_url=args.url,
            prepped_url=prepared_request.url,
        )
    if args.compress and prepared_request.body:
        compress_body(prepared_request, always=args.compress > 1)

    return prepared_request


def collect_messages(
    args: argparse.Namespace,
    config_dir: Path,
) -> Iterable[Union[requests.PreparedRequest, requests.Response]]:
    """
    Prepares request, sends it and follows redirects if specified
    Uses and updates the session file if specified

    Arguments:
        - args: arguments from CLI
        - config_dir: directory for the session files

    Returns: yields requests and responses
    """

    request_kwargs, send_kwargs, httpie_session, requests_session\
        = prepare_sessions(args, config_dir)

    if args.debug:
        # TODO: reflect the split between request and send kwargs.
        dump_request(request_kwargs)

    prepared_request = create_prepared_request(args, requests_session, request_kwargs)

    expired_cookies = []
    for response_count in range(1, args.max_redirects + 1):
        yield prepared_request
        if args.offline:
            break

        send_kwargs_merged = requests_session.merge_environment_settings(
            prepared_request.url,
            send_kwargs['proxies'],
            send_kwargs['stream'],
            send_kwargs['verify'],
            send_kwargs['cert'],
        )
        with max_headers(args.max_headers):
            response = requests_session.send(
                timeout=send_kwargs['timeout'],
                allow_redirects=send_kwargs['allow_redirects'],
                **send_kwargs_merged,
                request=prepared_request,
            )

        # noinspection PyProtectedMember
        expired_cookies += get_expired_cookies(
            headers=response.raw._original_response.msg._headers
        )

        if not response.next or not args.follow:
            yield response
            break

        prepared_request = follow_redirect(args, response_count, response)
        if not args.all:
            continue
        yield response

    if httpie_session:
        if httpie_session.is_new() or not args.session_read_only:
            httpie_session.update_cookies(requests_session.cookies, expired_cookies)


def follow_redirect(
    args: argparse.Namespace,
    response_count: int,
    response: requests.Response
) -> requests.Response:
    if args.max_redirects and response_count == (args.max_redirects):
        raise requests.TooManyRedirects
    return response.next


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
