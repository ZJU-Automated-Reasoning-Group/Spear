class A:
    def func(self):
        pass


class B:
    def func(self):
        pass


class C:
    x = A()


c1 = C()
c1.x = B()
c2 = C()
c2.x.func()
