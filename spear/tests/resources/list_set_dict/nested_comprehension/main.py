def func1():
    pass


def func2():
    pass


def func3():
    pass


a = [[func1], [func2], [func3]]
b = [f for l in a for f in l]

for func in b:
    func()
