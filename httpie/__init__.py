"""
HTTPie - a CLI, cURL-like tool for humans.

"""
__version__ = '1.0.3'
__author__ = 'Jakub Roztocil'
__licence__ = 'BSD'


class ExitStatus:
    """Program exit code constants."""
    SUCCESS = 0
    ERROR = 1
    PLUGIN_ERROR = 7

    # 128+2 SIGINT <http://www.tldp.org/LDP/abs/html/exitcodes.html>
    ERROR_CTRL_C = 130

    ERROR_TIMEOUT = 2
    ERROR_TOO_MANY_REDIRECTS = 6

    # Used only when requested with --check-status:
    ERROR_HTTP_3XX = 3
    ERROR_HTTP_4XX = 4
    ERROR_HTTP_5XX = 5


EXIT_STATUS_LABELS = {
    value: key
    for key, value in ExitStatus.__dict__.items()
    if key.isupper()
}
