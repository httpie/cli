class ConnectionError(Exception):
    def __init__(self, details, url, method):
        self.details = details
        self.url = url
        self.method = method
        self.reason = None
        self.hint = None

    def __str__(self):
        if ("[Errno 11001] getaddrinfo failed" in str(self.details) or   
            "[Errno -2] Name or service not known" in str(self.details) or 
            "[Errno 8] nodename nor servname " in str(self.details)): 
            self.reason = 'DNSLookupError'
            msg = (
                f'Connection from {self.url} aborted while doing a {self.method} request: {self.reason}'
            )
        else:
            msg = (
                f'Connection from {self.url} aborted while doing a {self.method} request'
            )
        return msg
