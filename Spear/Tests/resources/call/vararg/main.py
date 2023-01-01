def func(f0, *vararg):
    for f in vararg:
        f()


def f0():
    pass


def f1():
    pass


def f2():
    pass


func(f0, f1, f2)
