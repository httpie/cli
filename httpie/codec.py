from typing import Union

from charset_normalizer import from_bytes

from .constants import UTF8


def detect_encoding(content: bytes) -> str:
    """Detect the `content` encoding.
    Fallback to UTF-8 when no suitable encoding found.

    """
    match = from_bytes(bytes(content)).best()
    return match.encoding if match else UTF8


def decode(content: Union[bytearray, bytes], encoding: str) -> str:
    """Decode `content` using the given `encoding`.
    If no `encoding` is provided, the best effort is to guess it from `content`.

    Unicode errors are replaced.

    """
    if not encoding:
        encoding = detect_encoding(content)
    return content.decode(encoding, 'replace')
