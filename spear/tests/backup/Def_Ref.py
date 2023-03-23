# function defintion: 
# default parameter, variant parameter, keyword parameter

# nested function (3 levels): 
# nonlocal assignment
# global decalaration in outer function
# decalared global but is actually local


# class:
# defined in function: nonlocal
# class method
# global, nonlocal

# names reference and assign
# attribute reference and assign

def func(arg1, arg2=2, arg3=[]):
    a = arg1  # Const 0
    b = arg2  # 2
    c = arg3  # list, instance

    def func2(*args, **kwargs):
        return c.f

    class C:
        global b
        nonlocal c
        a = b  # C.a: 0, "b"
        c = a  # C

        def method(self):
            self.attr1 = c  # c.attr1 =
            self.attr2 = b
            return func2

    return C


b = func
c = func(0)()
_func2 = c.method()
_func2()
