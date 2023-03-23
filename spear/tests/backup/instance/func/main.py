def func1():
    pass


def func2():
    pass


class C:
    pass


c1 = C()
c2 = C()
c1.func = func1
c2.func = func2
c1.func()
