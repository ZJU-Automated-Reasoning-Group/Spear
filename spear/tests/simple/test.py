class A(object):
    def __init__(self, data):
        self.data = data


class B(object):
    def __init__(self, data):
        self.data = data


def bar(d):
    if d > 10:
        x = A(10)
    else:
        x = A(330)
    return x


ss = bar(33)