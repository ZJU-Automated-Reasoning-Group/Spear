class A:
    def func(self):
        pass


class B(A):
    def func(self):
        del B.func


b = B()
b.func()
b.func()
