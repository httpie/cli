from typing import Union, Tuple

from charset_normalizer import from_bytes
from charset_normalizer.constant import TOO_SMALL_SEQUENCE

UTF8 = 'utf-8'

ContentBytes = Union[bytearray, bytes]


def detect_encoding(content: ContentBytes) -> str:
    """
    We default to UTF-8 if text too short, because the detection
    can return a random encoding leading to confusing results
    given the `charset_normalizer` version (< 2.0.5).

    >>> too_short = ']"foo"'
    >>> detected = from_bytes(too_short.encode()).best().encoding
    >>> detected
    'ascii'
    >>> too_short.encode().decode(detected)
    ']"foo"'
    """
    encoding = UTF8
    if len(content) > TOO_SMALL_SEQUENCE:
        match = from_bytes(bytes(content)).best()
        if match:
            encoding = match.encoding
    return encoding


def smart_decode(content: ContentBytes, encoding: str) -> Tuple[str, str]:
    """Decode `content` using the given `encoding`.
    If no `encoding` is provided, the best effort is to guess it from `content`.

    Unicode errors are replaced.

    """
    if not encoding:
        encoding = detect_encoding(content)
    return content.decode(encoding, 'replace'), encoding


def smart_encode(content: str, encoding: str) -> bytes:
    """Encode `content` using the given `encoding`.

    Unicode errors are replaced.

    """
    return content.encode(encoding, 'replace')
