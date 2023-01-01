class A:
    @staticmethod
    def func(arg):
        arg()


class B(A):
    pass


def arg():
    pass


B().func(arg)
