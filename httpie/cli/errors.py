class CustomError(Exception):
    def __init__(self, *args, **kwargs):
        super.__init__
        self.exc = None
        self.message = None
        self.details = None
        self.args = None
        self.hint = None
        self.support = None

    def __str__(self):
        pass