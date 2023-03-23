def func(f):
    def nested():
        f()

    return nested


def f0():
    pass


def f1():
    pass


func(f0)()
func(f1)()
