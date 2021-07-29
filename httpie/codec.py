from typing import Union

from charset_normalizer import from_bytes

from .constants import UTF8


def detect(content: bytes) -> str:
    """Detect the `content` charset encoding.
    Fallback to UTF-8 when no suitable encoding found.

    """
    match = from_bytes(bytes(content)).best()
    return match.encoding if match else UTF8


class TextDecoderStrategy:
    """Content decoding strategy.

    """

    def __init__(self, encoding: str):
        self.encoding = encoding

    def get_encoding(self, content: bytes) -> str:
        """Return the `content` charset encoding.

        """
        return self.encoding or detect(content)

    def decode(self, content: Union[bytearray, bytes, str]) -> str:
        """Decode `content`. Unicode errors are replaced.

        """
        if isinstance(content, str):
            return content
        return content.decode(self.get_encoding(content), 'replace')
