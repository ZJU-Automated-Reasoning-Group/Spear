# nested function: local, global, nonlocal
# class attribute, method call
def getF(obj):
    return obj.f


def getG(obj):
    return obj.g


class C:
    def __init__(self, f, g):
        self.f = f
        self.g = g

    def method(self, func):
        return func(self)


def func(arg):
    nl = 0  # nl should be 0, ins

    def func2(getter):
        return nl.method(getter)

    def assign():
        nonlocal nl
        nl = arg

    assign()
    return func2


lower = C("f", "g")  # instance
upper = C("F", "G")  # instance
f = func(lower)(getF)
G = func(upper)(getG)
