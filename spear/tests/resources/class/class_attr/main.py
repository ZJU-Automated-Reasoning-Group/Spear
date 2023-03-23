def func1():
    pass


def func2():
    pass


def func3():
    pass


class C:
    l = [func1, func2, func3]

    def __init__(self):
        for func in self.l:
            func()


C()
