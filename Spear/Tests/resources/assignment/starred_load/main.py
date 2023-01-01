def func1():
    pass


def func2():
    pass


def func3():
    pass


def func4():
    pass


l = [func2, func3]

a = func1, *l, func4

for f in a:
    f()
