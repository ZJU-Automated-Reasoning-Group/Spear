def func():
    def g(self):
        pass

    class A:
        global g
        f = g

    class B:
        global C
        C = A


def g(self):
    pass


func()

C().f()
