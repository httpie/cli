from typing import Union

from charset_normalizer import from_bytes
from charset_normalizer.constant import TOO_SMALL_SEQUENCE

UTF8 = 'utf-8'

ContentBytes = Union[bytearray, bytes]


def detect_encoding(content: ContentBytes) -> str:
    """
    We default to utf8 if text too short, because the detection
    can return a random encoding leading to confusing results:

    >>> too_short = ']"foo"'
    >>> detected = from_bytes(too_short.encode()).best().encoding
    >>> detected
    'utf_16_be'
    >>> too_short.encode().decode(detected)
    '崢景漢'

    """
    encoding = UTF8
    if len(content) > TOO_SMALL_SEQUENCE:
        match = from_bytes(bytes(content)).best()
        if match:
            encoding = match.encoding
    return encoding


def smart_decode(content: ContentBytes, encoding: str) -> str:
    """Decode `content` using the given `encoding`.
    If no `encoding` is provided, the best effort is to guess it from `content`.

    Unicode errors are replaced.

    """
    if not encoding:
        encoding = detect_encoding(content)
    return content.decode(encoding, 'replace')


def smart_encode(content: str, encoding: str) -> bytes:
    """Encode `content` using the given `encoding`.

    Unicode errors are replaced.

    """
    return content.encode(encoding, 'replace')
