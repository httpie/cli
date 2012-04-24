from requests.compat import urlparse


class HTTPMessage(object):
    """Model representing an HTTP message."""

    def __init__(self, line, headers, body, content_type=None):
        # {Request,Status}-Line
        self.line = line
        self.headers = headers
        self.body = body
        self.content_type = content_type


def from_request(request):
    """Make an `HTTPMessage` from `requests.models.Request`."""
    url = urlparse(request.url)
    request_headers = dict(request.headers)
    if 'Host' not in request_headers:
        request_headers['Host'] = url.netloc
    return HTTPMessage(
        line='{method} {path} HTTP/1.1'.format(
                method=request.method,
                path=url.path or '/'),
        headers='\n'.join(str('%s: %s') % (name, value)
                          for name, value
                          in request_headers.items()),
        body=request._enc_data,
        content_type=request_headers.get('Content-Type')
    )


def from_response(response):
    """Make an `HTTPMessage` from `requests.models.Response`."""
    encoding = response.encoding or 'ISO-8859-1'
    original = response.raw._original_response
    response_headers = response.headers
    return HTTPMessage(
        line='HTTP/{version} {status} {reason}'.format(
                version='.'.join(str(original.version)),
                status=original.status, reason=original.reason,),
        headers=str(original.msg),
        body=response.content.decode(encoding) if response.content else '',
        content_type=response_headers.get('Content-Type'))


def format(message, prettifier=None,
           with_headers=True, with_body=True):
    """Return a `unicode` representation of `message`. """
    bits = []
    if with_headers:
        if prettifier:
            bits.append(prettifier.headers(message.line))
            bits.append(prettifier.headers(message.headers))
        else:
            bits.append(message.line)
            bits.append(message.headers)
        if with_body and message.body:
            bits.append('\n')
    if with_body and message.body:
        if prettifier and message.content_type:
            bits.append(prettifier.body(message.body, message.content_type))
        else:
            bits.append(message.body)
    bits.append('\n')
    return '\n'.join(bit.strip() for bit in bits)
