import socket


class CustomResolver:
    @staticmethod
    def parse_resolve_entry(entry):
        """
        :param entry:
        :return: host, port (or `None` if absent) and
        """
        host, port_and_addresses = entry.split(':', 1)
        try:
            # If port is not absent, e.g. 'example.org:80:127.0.0.1'
            port, addresses = port_and_addresses.split(':', 1)
            port = int(port)
        except ValueError:
            port = None
            addresses = port_and_addresses

        return host, port, [
            a[1:-1] if a.startswith('[') and a.endswith(']') else a
            for a in addresses.split(',')
        ]

    def __init__(self, resolve):
        """
        :param resolve: A list of HOST[:PORT]:ADDRESS[:ADDRESS]? records
        :type resolve: list[str]
        """
        self.entries = {
            (host, port): addresses
            for host, port, addresses in map(self.parse_resolve_entry, resolve)
        }

    def getaddrinfo(self, host, port, family=None, socktype=None, proto=None, flags=None):
        for key in [(host, port), (host, None)]:
            if key in self.entries:
                return [
                    res
                    for ip in self.entries[key]
                    for res in self._original_getaddrinfo(ip, port, family, socktype, proto or 0, flags or 0)
                ]
        else:
            v = self._original_getaddrinfo(host, port, family, socktype, proto or 0, flags or 0)
            return v

    def __enter__(self):
        self._original_getaddrinfo = socket.getaddrinfo
        if self.entries:
                socket.getaddrinfo = lambda host, port, *args, **kwargs: self.getaddrinfo(host, port, *args, **kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        socket.getaddrinfo = self._original_getaddrinfo


__all__ = ['CustomResolver']
