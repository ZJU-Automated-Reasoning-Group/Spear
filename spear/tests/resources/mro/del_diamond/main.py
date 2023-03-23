class A:
    def __init__(self):
        pass

    def func(self):
        pass


class B(A):
    pass


class C(A):
    def func(self):
        del C.func


class D(B, C):
    pass


d = D()
d.func()
d.func()
