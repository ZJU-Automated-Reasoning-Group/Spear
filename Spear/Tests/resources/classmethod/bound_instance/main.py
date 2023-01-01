class A:
    @classmethod
    def method(cls):
        cls.func()


class B(A):
    @staticmethod
    def func():
        pass


class C(A):
    @staticmethod
    def func():
        pass


c = C()
c.method()
