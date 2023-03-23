def func1():
    pass


def func2():
    pass


def getF(arg):
    var = 0

    def inner():
        var2 = arg.f

        def move():
            nonlocal var
            var = var2

        move()

    inner()
    return var


class C:
    pass


c1 = C()
c1.f = func1

c2 = C()
c2.f = func2

f1 = getF(c1)
f2 = getF(c2)

f1()
