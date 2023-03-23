def func():
    nl = 0

    class C:
        nonlocal nl

        def f(self):
            pass

        nl = f

    nl(C())


func()
