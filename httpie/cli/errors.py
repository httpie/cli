class Error(Exception):
    '''Base Class for custom exceptions'''
    def __init__(self, *args, **kwargs):
        super().__init__(self,*args, **kwargs)
    #TODO: Do I need to define custom methods/attributes for Error class or is *args, **kwargs,and built-in methods from Exception class sufficient?

class ConnectionError(Error):
    #TODO: Work on this class together
    '''Exception raised for error when connecting to server'''
    pass

class BasicAuthError(Error):
    '''Exception raised for wrong username and pw when authenticating'''
    #TODO: may need to account for different auth types within this class
    pass

class MethodMismatchError(Error):
    '''Exception raised when the wrong method is used with the wrong URL request'''
    pass

class LocalHostError(Error):
    '''Exception raised when the user fails to provide a valid localhost'''
    pass

#TODO: ADD the rest of the classes including a general catch-all one for errors we may miss
#TODO: Write tests for intended class functionctionality