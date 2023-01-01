def func():
    def g(self):
        pass

    class C:
        f = g
        g = gg
        ff = g

    return C


def gg(self):
    pass


C = func()
C.f()
C.ff()
