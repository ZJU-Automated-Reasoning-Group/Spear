def func(arg):
    def inner():
        g()
        arg()

    inner()


def g():
    pass


def gg():
    pass


func(gg)
