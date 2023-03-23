class A:
    @staticmethod
    def func(arg):
        arg(print)


A.func(A.func)
