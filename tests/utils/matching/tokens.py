from enum import Enum, auto


class Expect(Enum):
    """
    Predefined token types we can expect in the output.

    """
    REQUEST_HEADERS = auto()
    RESPONSE_HEADERS = auto()
    RESPONSE_META = auto()
    BODY = auto()
    SEPARATOR = auto()


class ExpectSequence:
    """
    Standard combined chunks. These predefined requests and responses assume a body.

    """
    RAW_REQUEST = [
        Expect.REQUEST_HEADERS,
        Expect.BODY,
    ]
    RAW_RESPONSE = [
        Expect.RESPONSE_HEADERS,
        Expect.BODY,
    ]
    RAW_EXCHANGE = [
        *RAW_REQUEST,
        Expect.SEPARATOR,  # Good choice?
        *RAW_RESPONSE,
    ]
    RAW_BODY = [
        Expect.BODY,
    ]
    TERMINAL_REQUEST = [
        *RAW_REQUEST,
        Expect.SEPARATOR,
    ]
    TERMINAL_RESPONSE = [
        *RAW_RESPONSE,
        Expect.SEPARATOR,
    ]
    TERMINAL_EXCHANGE = [
        *TERMINAL_REQUEST,
        *TERMINAL_RESPONSE,
    ]
    TERMINAL_EXCHANGE_META = [
        *TERMINAL_EXCHANGE,
        Expect.RESPONSE_META
    ]
    TERMINAL_BODY = [
        RAW_BODY,
        Expect.SEPARATOR
    ]
