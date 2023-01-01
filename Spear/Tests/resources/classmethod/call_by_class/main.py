class A:
    @classmethod
    def method(cls):
        pass


class B(A):
    pass


B.method()
