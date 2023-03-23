def func1():
    pass


def func2():
    pass


class A:
    def start(self, func):
        self.m1(func)

    def m1(self, func):
        self.m2(func)

    def m2(self, func):
        self.m3(func)


class B(A):
    def m3(self, func):
        func()


class C(A):
    def m3(self, func):
        func()


b = B()
c = C()
b.start(func1)
c.start(func2)
