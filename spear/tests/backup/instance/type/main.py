class E1:
    def m(self):
        pass


class E2:
    def m(self):
        pass


class C:
    pass


c1 = C()
c1.e = E1()

c2 = C()
c2.e = E2()

c1.e.m()
