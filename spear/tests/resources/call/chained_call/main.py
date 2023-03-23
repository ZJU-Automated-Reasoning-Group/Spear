def func3():
    pass


def func2(a):
    a()


def func1(a, b=func2):
    a(b)


func1(func2)
func1(func2, func3)
