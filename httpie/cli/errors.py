class ConnectionError(Exception):
    def __init__(self, details, url, method, error_type):
        self.details = details
        self.url = url
        self.method = method
        self.reason = None
        self.error_type = error_type

    def __str__(self):
        if ("[Errno 11001] getaddrinfo failed" in str(self.details)
                or "[Errno -2] Name or service not known" in str(self.details)
                or "[Errno 8] nodename nor servname" in str(self.details)):
            self.reason = 'DNSLookupError'
            msg = (
                f'{self.error_type}'
                f'\nConnection from {self.url} aborted while doing a {self.method} request'
                f'\nReason: {self.reason}'
                f'\nDetails: {self.prettify_details(self.details)}'
            )
        else:
            msg = (
                f'Connection from {self.url} aborted while doing a {self.method} request'
            )
        return msg

    def prettify_details(self, details):
        if self.details:
            str_details = str(self.details)
            details = str_details.split(':')
            formatted_details = '.'.join([n for n in details if n != details[2]])
        return formatted_details
