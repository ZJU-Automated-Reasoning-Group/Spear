# many kinds of arguments / parameters pair 
# method


def func(arg1, /, arg2, arg3=0, *args, arg4=0, arg5, **kwargs):
    # print(posonlyarg)
    # print(arg12)
    # print(arg3)
    # print(arg4)
    # print(arg5)
    # for arg in args:
    #     print(arg)
    # for kw, arg in kwargs.items():
    #     print(f"{kw}:{arg}")
    # print("")
    pass


func(1, 2, arg5=5)
func(11, 22, arg5=55)

func(1, 2, 3, arg5=5)
func(11, 22, 33, arg5=55)

func(1, 2, arg5=5, arg4=4, arg3=3)
func(11, 22, arg5=55, arg4=44, arg3=33)

func(1, 2, 3, 6, 7, arg5=5, arg4=4, arg8=8, arg9=9)
func(11, 22, 33, 66, 77, arg5=55, arg4=44, arg8=88, arg9=99)
