class A:
    def __init__(self):
        pass


class B(A):
    def __init__(self):
        super().__init__()


class C(A):
    def __init__(self):
        super().__init__()


class D(C, B):
    def __init__(self):
        super().__init__()


D()
