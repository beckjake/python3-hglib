class CommandError(Exception):
    def __init__(self, args, ret, out, err):
        self.args = args
        self.ret = ret
        self.out = out
        self.err = err

class ServerError(Exception):
    pass

class ResponseError(ServerError, ValueError):
    pass

class CapabilityError(ServerError):
    pass
