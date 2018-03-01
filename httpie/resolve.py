import socket


class CustomResolver:
    def __init__(self, resolve):
        """
        :param resolve: A list of HOST[:PORT]:ADDRESS[:ADDRESS]? records
        :type resolve: list[str]
        """
        self.entries = {}
        for entry in resolve:
            host, port_and_addresses = entry.split(':', 1)
            if ':' in port_and_addresses:
                port, addresses = port_and_addresses.split(':', 1)
                try:
                    port = int(port)
                except ValueError:
                    port = None
                    addresses = port_and_addresses
            else:
                port = None
                addresses = port_and_addresses

            final_addresses = []
            for address in addresses.split(','):
                if address[:1] == '[' and address[-1:] == ']':
                    address = address[1:-1]
                final_addresses.append(address)
            self.entries[(host, port)] = final_addresses

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
