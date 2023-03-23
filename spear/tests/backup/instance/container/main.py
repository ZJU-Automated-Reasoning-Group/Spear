class E1:
    def m(self):
        pass


class E2:
    def m(self):
        pass


class C:
    def forAll(self):
        for e in self.elts:
            e.m()


c1 = C()
c1.elts = [E1(), E1(), E1()]

c2 = C()
c2.elts = [E2(), E2(), E2()]

c1.forAll()
