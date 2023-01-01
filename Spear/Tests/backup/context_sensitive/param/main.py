def func1():
    pass


def func2():
    pass


def caller1(f):
    f()


def caller2(f):
    f()


def callCaller(f, arg):
    f(arg)


callCaller(caller1, func1)
callCaller(caller2, func2)
