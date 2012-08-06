import os
import sys
from requests.compat import urlparse, is_windows, bytes, str


class Environment(object):
    """Holds information about the execution context.

    Groups various aspects of the environment in a changeable object
    and allows for mocking.

    """

    #noinspection PyUnresolvedReferences
    is_windows = is_windows

    progname = os.path.basename(sys.argv[0])
    if progname not in ['http', 'https']:
        progname = 'http'

    if is_windows:
        import colorama.initialise
        colorama.initialise.init()

    stdin_isatty = sys.stdin.isatty()
    stdin = sys.stdin
    stdout_isatty = sys.stdout.isatty()
    stdout = sys.stdout
    stderr = sys.stderr

    # Can be set to 0 to disable colors completely.
    colors = 256 if '256color' in os.environ.get('TERM', '') else 88

    def __init__(self, **kwargs):
        assert all(hasattr(type(self), attr)
                   for attr in kwargs.keys())
        self.__dict__.update(**kwargs)


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
        ct = self._orig.headers.get('Content-Type', '')
        if isinstance(ct, bytes):
            ct = ct.decode()
        return ct


class HTTPResponse(HTTPMessage):
    """A :class:`requests.models.Response` wrapper."""

    def iter_body(self, chunk_size=1):
        return self._orig.iter_content(chunk_size=chunk_size)

    def iter_lines(self, chunk_size):
        for line in self._orig.iter_lines(chunk_size):
            yield line, b'\n'

    @property
    def headers(self):
        original = self._orig.raw._original_response
        status_line = 'HTTP/{version} {status} {reason}'.format(
             version='.'.join(str(original.version)),
             status=original.status,
             reason=original.reason
         )
        headers = str(original.msg)
        return '\n'.join([status_line, headers]).strip()

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
        """Return Request-Line"""
        url = urlparse(self._orig.url)

        # Querystring
        qs = ''
        if url.query or self._orig.params:
            qs = '?'
            if url.query:
                qs += url.query
            # Requests doesn't make params part of ``request.url``.
            if self._orig.params:
                if url.query:
                    qs += '&'
                #noinspection PyUnresolvedReferences
                qs += type(self._orig)._encode_params(self._orig.params)

        # Request-Line
        request_line = '{method} {path}{query} HTTP/1.1'.format(
            method=self._orig.method,
            path=url.path or '/',
            query=qs
        )

        headers = dict(self._orig.headers)

        if 'Host' not in headers:
            headers['Host'] = urlparse(self._orig.url).netloc

        headers = ['%s: %s' % (name, value)
                   for name, value in headers.items()]

        headers.insert(0, request_line)

        return '\n'.join(headers).strip()

    @property
    def encoding(self):
        return 'utf8'

    @property
    def body(self):
        """Reconstruct and return the original request body bytes."""
        if self._orig.files:
            # TODO: would be nice if we didn't need to encode the files again
            # FIXME: Also the boundary header doesn't match the one used.
            for fn, fd in self._orig.files.values():
                # Rewind the files as they have already been read before.
                fd.seek(0)
            body, _ = self._orig._encode_files(self._orig.files)
        else:
            try:
                body = self._orig.data
            except AttributeError:
                # requests < 0.12.1
                body = self._orig._enc_data

            if isinstance(body, dict):
                #noinspection PyUnresolvedReferences
                body = type(self._orig)._encode_params(body)

            if isinstance(body, str):
                body = body.encode('utf8')

        return body
