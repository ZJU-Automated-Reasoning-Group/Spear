def identity(num):
    return num


n1 = identity(1)  # 1
n2 = identity(2)  # 2


# print(n1)
# print(n2)

def newGenerator(l):
    def next():
        yield from l

    return next


gen1 = newGenerator([1, 2, 3])
gen2 = newGenerator([4, 5, 6])
for e1 in gen1():  # 1, 2, 3
    # print(e1)
    pass

for e2 in gen2():  # 4, 5, 6
    # print(e2)
    pass


def getClass(f):
    class C:
        f = f

    return C


c1 = getClass(1)()
f1 = c1.f
c2 = getClass(2)()
f2 = c2.f
