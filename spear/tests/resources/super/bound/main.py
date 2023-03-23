class A:
    def __init__(self):
        super().__init__()


class B:
    def __init__(self):
        self.func()


class C:
    def __init__(self):
        self.func()


class D(A, B):
    def __init__(self):
        super().__init__()

    def func(self):
        pass


class E(A, C):
    def __init__(self):
        super().__init__()

    def func(self):
        pass


D()
E()
