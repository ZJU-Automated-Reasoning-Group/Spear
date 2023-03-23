# call: args, keywords
# call a class
def foo(a, b=1, /, c=2, *args, **kwargs):
    pass


class C:
    def __init__(self, a, b=1):
        pass


c = C(foo(1, b=[]), b=2)
