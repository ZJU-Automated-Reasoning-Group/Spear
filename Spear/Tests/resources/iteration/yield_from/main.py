def func1():
    pass


def func2():
    pass


def func3():
    pass


def getFunc():
    yield func1
    yield func2
    yield func3


def getFunc2():
    yield from getFunc()


for f in getFunc2():
    f()
