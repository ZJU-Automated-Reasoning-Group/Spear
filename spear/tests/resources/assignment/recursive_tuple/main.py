def func1():
    pass


def func2():
    pass


def func3():
    pass


def func4():
    pass


def func5():
    pass


def func6():
    pass


a, (b, (c, d)) = func1, (func2, (func3, func4))
a()
b()
d()
