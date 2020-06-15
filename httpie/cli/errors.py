class Error(Exception):
    '''Base Class for custom exceptions'''
    def __init__(self, *args, **kwargs):
        super().__init__(self,*args, **kwargs)

class ConnectionError(Error):
    def __init__(self, *args):
        self.exc = None
        self.message = None

    def info(self, method):
        self.message = f"Connection failed while doing a {method} request to URL:"
        return self.message
