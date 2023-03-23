def func1():
    pass


def func2():
    pass


def func3():
    pass


def func4():
    pass


def func5():
    pass


def func6():
    pass


l = [func1, func2]
s = {func3, func4}
d = {func5: None, func6: None}

for f1 in l:
    f1()

for f2 in s:
    f2()

for f3 in d:
    f3()
