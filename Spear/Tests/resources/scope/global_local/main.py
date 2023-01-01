def func():
    global g

    def inner(arg):
        g = arg

    inner(inner)


def g():
    pass


func()
g()
