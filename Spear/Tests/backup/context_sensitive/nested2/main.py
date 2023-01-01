def func1():
    pass


def func2():
    pass


def save(func):
    def get():
        return func

    return get


get1 = save(func1)
get2 = save(func2)
f = get1()
f()
