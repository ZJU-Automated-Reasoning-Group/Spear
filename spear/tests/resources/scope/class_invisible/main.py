def func(self):
    pass


def func2(self):
    pass


class C:
    func = func2

    def method(self):
        func()

    class D:
        method = func


C.method()
C.D.method()
