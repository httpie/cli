from enum import IntEnum, unique


@unique
class ExitStatus(IntEnum):
    """Program exit status code constants."""
    SUCCESS = 0
    ERROR = 1
    ERROR_TIMEOUT = 2

    # See --check-status
    ERROR_HTTP_3XX = 3
    ERROR_HTTP_4XX = 4
    ERROR_HTTP_5XX = 5

    ERROR_TOO_MANY_REDIRECTS = 6
    PLUGIN_ERROR = 7
    # 128+2 SIGINT
    # <http://www.tldp.org/LDP/abs/html/exitcodes.html>
    ERROR_CTRL_C = 130


def http_status_to_exit_status(http_status: int, follow=False) -> ExitStatus:
    """
    Translate HTTP status code to exit status code.

    (Relevant only when invoked with --check-status or --download.)

    """
    if 300 <= http_status <= 399 and not follow:
        # Redirect
        return ExitStatus.ERROR_HTTP_3XX
    elif 400 <= http_status <= 499:
        # Client Error
        return ExitStatus.ERROR_HTTP_4XX
    elif 500 <= http_status <= 599:
        # Server Error
        return ExitStatus.ERROR_HTTP_5XX
    else:
        return ExitStatus.SUCCESS
