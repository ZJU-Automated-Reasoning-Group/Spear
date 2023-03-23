# muliple inhirent
# same name multiple class
# instance resolve
# delattr

# simple inheritence
class A0:
    def foo(self):
        return "A0.foo"


class B0(A0):
    def foo(self):
        return "B0.foo"


ins0 = B0()
ret0 = ins0.foo()  # should only be "B0.foo"
print(ret0)


# multiple inheritence: diamond
class A1:
    def foo(self):
        return "A1.foo"


class B1(A1):
    pass


class C1(A1):
    def foo(self):
        return "C1.foo"


class D1(B1, C1):
    pass


ins1 = D1()
ret1 = ins1.foo()  # should only be "C1.foo"
print(ret1)


# multiple inheritence: diamond
class A2:
    def foo(self):
        return "A2.foo"


class B2(A2):
    pass


class C2(A2):
    def foo(self):
        return "C2.foo"


class D2(B2, C2):
    pass


ins2 = D2()
del C2.foo
ret2 = ins2.foo()  # should be "C2.foo", "A2.foo"
print(ret2)


# same name multiple class
class A3:
    def foo(self):
        return "A3.foo"


class B3(A3):
    def foo(self):
        return "B3.foo"


class C3(A3):
    def foo(self):
        return "C3.foo"


if True:

    class D3(B3, C3):
        pass
else:
    class D3(C3, B3):
        pass

ins3 = D3()
ret3 = ins3.foo()  # should be "B3.foo", "C3.foo"
print(ret3)
