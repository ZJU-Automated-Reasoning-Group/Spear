class A:
    def func(self):
        pass


class B(A):
    pass


def funcB(self):
    pass


b = B()
b.func()
B.func = funcB
b.func()
