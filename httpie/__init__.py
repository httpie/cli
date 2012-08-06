"""
HTTPie - cURL for humans.

"""
__author__ = 'Jakub Roztocil'
__version__ = '0.2.7'
__licence__ = 'BSD'


class EXIT:
    OK = 0
    ERROR = 1
    # Used only when requested:
    ERROR_HTTP_3XX = 3
    ERROR_HTTP_4XX = 4
    ERROR_HTTP_5XX = 5
