from __future__ import division


def humanize_bytes(n, precision=2):
    # Author: Doug Latornell
    # Licence: MIT
    # URL: http://code.activestate.com/recipes/577081/
    """Return a humanized string representation of a number of bytes.

    Assumes `from __future__ import division`.

    >>> humanize_bytes(1)
    '1 byte'
    >>> humanize_bytes(1024)
    '1.0 kB'
    >>> humanize_bytes(1024 * 123)
    '123.0 kB'
    >>> humanize_bytes(1024 * 12342)
    '12.1 MB'
    >>> humanize_bytes(1024 * 12342, 2)
    '12.05 MB'
    >>> humanize_bytes(1024 * 1234, 2)
    '1.21 MB'
    >>> humanize_bytes(1024 * 1234 * 1111, 2)
    '1.31 GB'
    >>> humanize_bytes(1024 * 1234 * 1111, 1)
    '1.3 GB'

    """
    abbrevs = [
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'B')
    ]

    if n == 1:
        return '1 B'

    for factor, suffix in abbrevs:
        if n >= factor:
            break

    return '%.*f %s' % (precision, n / factor, suffix)
