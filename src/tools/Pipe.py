class Pipe:
    def __init__(self, data):
        self.data = data
        self.operations: list = []

    def do(self, func, *args, **kwargs):
        self.operations.append(("do", func, args, kwargs))
        return self

    def to(self, tran):
        self.operations.append(("to", tran))
        return self

    def get(self):
        result = self.data
        for op in self.operations:
            if op[0] == "do":
                func, args, kwargs = op[1], op[2], op[3]
                actual_args = tuple([result if x is ... else x for x in args])
                result = func(*actual_args, **kwargs)
            elif op[0] == "to":
                result = op[1](result)
        return result
