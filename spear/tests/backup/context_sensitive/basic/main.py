def func1():
    pass


def func2():
    pass


def transfer(c):
    c.f = c.g


class C:
    pass


c1 = C()
c1.g = func1
c2 = C()
c2.g = func2
transfer(c1)
transfer(c2)
c1.f()
