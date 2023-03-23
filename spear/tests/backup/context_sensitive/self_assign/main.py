def func1():
    pass


def func2():
    pass


class Wrapper:
    def __init__(self, func):
        self.set(func)

    def set(self, func):
        self.doSet(func)

    def doSet(self, func):
        self.func = func

    def get(self):
        return self.func


c1 = Wrapper(func1)
c2 = Wrapper(func2)
c1.get()()
