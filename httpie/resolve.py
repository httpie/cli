import socket


class CustomResolver:
    def __init__(self, resolve):
        """
        :param resolve: A list of HOST:PORT:ADDRESS[:ADDRESS]? records
        :type resolve: list[str]
        """
        self.entries = {}
        for entry in resolve:
            host, port, addresses = entry.split(':', 2)
            final_addresses = []
            for address in addresses.split(','):
                if address[:1] == '[' and address[-1:] == ']':
                    address = address[1:-1]
                final_addresses.append(address)
            self.entries[(host, int(port))] = final_addresses

    def getaddrinfo(self, host, port, family=None, socktype=None, proto=None, flags=None):
        key = (host, port)
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
        socket.getaddrinfo = lambda host, port, *args, **kwargs: self.getaddrinfo(host, port, *args, **kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        socket.getaddrinfo = self._original_getaddrinfo


__all__ = ['CustomResolver']
