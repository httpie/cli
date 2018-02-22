import json
import sys

import requests
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict

from httpie import sessions
from httpie import __version__
from httpie.compat import str
from httpie.input import SSL_VERSION_ARG_MAPPING
from httpie.plugins import plugin_manager
from httpie.utils import repr_dict_nice

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
JSON_ACCEPT = '{0}, */*'.format(JSON_CONTENT_TYPE)
DEFAULT_UA = 'HTTPie/%s' % __version__


class HTTPieHTTPAdapter(HTTPAdapter):

    def __init__(self, ssl_version=None, **kwargs):
        self._ssl_version = ssl_version
        super(HTTPieHTTPAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_version'] = self._ssl_version
        super(HTTPieHTTPAdapter, self).init_poolmanager(*args, **kwargs)


def get_requests_session(ssl_version):
    requests_session = requests.Session()
    requests_session.mount(
        'https://',
        HTTPieHTTPAdapter(ssl_version=ssl_version)
    )
    for cls in plugin_manager.get_transport_plugins():
        transport_plugin = cls()
        requests_session.mount(prefix=transport_plugin.prefix,
                               adapter=transport_plugin.get_adapter())
    return requests_session


def get_response(args, config_dir):
    """Send the request and return a `request.Response`."""

    ssl_version = None
    if args.ssl_version:
        ssl_version = SSL_VERSION_ARG_MAPPING[args.ssl_version]

    requests_session = get_requests_session(ssl_version)
    requests_session.max_redirects = args.max_redirects

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


def dump_request(kwargs):
    sys.stderr.write('\n>>> requests.request(**%s)\n\n'
                     % repr_dict_nice(kwargs))


def finalize_headers(headers):
    final_headers = {}
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


def get_default_headers(args):
    default_headers = CaseInsensitiveDict({
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


def get_requests_kwargs(args, base_headers=None):
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
        'timeout': args.timeout,
        'auth': args.auth,
        'proxies': {p.key: p.value for p in args.proxy},
        'files': args.files,
        'allow_redirects': args.follow,
        'params': args.params,
    }

    return kwargs
