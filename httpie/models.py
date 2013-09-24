import os
import sys

from .config import DEFAULT_CONFIG_DIR, Config
from .compat import urlsplit, is_windows, bytes, str


class Environment(object):
    """Holds information about the execution context.

    Groups various aspects of the environment in a changeable object
    and allows for mocking.

    """

    is_windows = is_windows

    progname = os.path.basename(sys.argv[0])
    if progname not in ['http', 'https']:
        progname = 'http'

    config_dir = DEFAULT_CONFIG_DIR

    # Can be set to 0 to disable colors completely.
    colors = 256 if '256color' in os.environ.get('TERM', '') else 88

    stdin = sys.stdin
    stdin_isatty = sys.stdin.isatty()

    stdout_isatty = sys.stdout.isatty()
    stderr_isatty = sys.stderr.isatty()
    if is_windows:
        # noinspection PyUnresolvedReferences
        from colorama.initialise import wrap_stream
        stdout = wrap_stream(sys.stdout, convert=None,
                             strip=None, autoreset=True, wrap=True)
        stderr = wrap_stream(sys.stderr, convert=None,
                             strip=None, autoreset=True, wrap=True)
    else:
        stdout = sys.stdout
        stderr = sys.stderr

    def __init__(self, **kwargs):
        assert all(hasattr(type(self), attr)
                   for attr in kwargs.keys())
        self.__dict__.update(**kwargs)

    @property
    def config(self):
        if not hasattr(self, '_config'):
            self._config = Config(directory=self.config_dir)
            if self._config.is_new:
                self._config.save()
            else:
                self._config.load()
        return self._config


class HTTPMessage(object):
    """Abstract class for HTTP messages."""

    def __init__(self, orig):
        self._orig = orig

    def iter_body(self, chunk_size):
        """Return an iterator over the body."""
        raise NotImplementedError()

    def iter_lines(self, chunk_size):
        """Return an iterator over the body yielding (`line`, `line_feed`)."""
        raise NotImplementedError()

    @property
    def headers(self):
        """Return a `str` with the message's headers."""
        raise NotImplementedError()

    @property
    def encoding(self):
        """Return a `str` with the message's encoding, if known."""
        raise NotImplementedError()

    @property
    def body(self):
        """Return a `bytes` with the message's body."""
        raise NotImplementedError()

    @property
    def content_type(self):
        """Return the message content type."""
        return self._orig.headers.get('Content-Type', '')


class HTTPResponse(HTTPMessage):
    """A :class:`requests.models.Response` wrapper."""

    def iter_body(self, chunk_size=1):
        return self._orig.iter_content(chunk_size=chunk_size)

    def iter_lines(self, chunk_size):
        return ((line, b'\n') for line in self._orig.iter_lines(chunk_size))

    #noinspection PyProtectedMember
    @property
    def headers(self):
        original = self._orig.raw._original_response
        status_line = 'HTTP/{version} {status} {reason}'.format(
            version='.'.join(str(original.version)),
            status=original.status,
            reason=original.reason
        )
        headers = [status_line]
        try:
            # `original.msg` is a `http.client.HTTPMessage` on Python 3
            # `_headers` is a 2-tuple
            headers.extend(
                '%s: %s' % header for header in original.msg._headers)
        except AttributeError:
            # and a `httplib.HTTPMessage` on Python 2.x
            # `headers` is a list of `name: val<CRLF>`.
            headers.extend(h.strip() for h in original.msg.headers)

        return '\r\n'.join(headers)

    @property
    def encoding(self):
        return self._orig.encoding or 'utf8'

    @property
    def body(self):
        # Only now the response body is fetched.
        # Shouldn't be touched unless the body is actually needed.
        return self._orig.content


class HTTPRequest(HTTPMessage):
    """A :class:`requests.models.Request` wrapper."""

    def iter_body(self, chunk_size):
        yield self.body

    def iter_lines(self, chunk_size):
        yield self.body, b''

    @property
    def headers(self):
        url = urlsplit(self._orig.url)

        request_line = '{method} {path}{query} HTTP/1.1'.format(
            method=self._orig.method,
            path=url.path or '/',
            query='?' + url.query if url.query else ''
        )

        headers = dict(self._orig.headers)

        if 'Host' not in headers:
            headers['Host'] = url.netloc

        headers = ['%s: %s' % (name, value)
                   for name, value in headers.items()]

        headers.insert(0, request_line)

        return '\r\n'.join(headers).strip()

    @property
    def encoding(self):
        return 'utf8'

    @property
    def body(self):
        body = self._orig.body
        if isinstance(body, str):
            # Happens with JSON/form request data parsed from the command line.
            body = body.encode('utf8')
        return body or b''
