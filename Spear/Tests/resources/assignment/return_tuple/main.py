def func1(f):
    f()


def func2(f):
    f()


def reverse(x, y):
    return y, x


x, y = reverse(func1, func2)
x(y)
