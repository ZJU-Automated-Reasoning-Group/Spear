# List, Tuple, Dict, Set iteration
# generator: yield, yield from

a = [1, 2, 3]
b = (1, 2, 3)
c = {1: "1", 2: "2", 3: "3"}


def gen1():
    for s in a:
        ret = yield s

    return ret


def gen2():
    yield from a


for v in a:
    pass

for v in b:
    pass
for v in c:
    pass
gen1().send("A")
for v in gen1():
    pass

for v in gen2():
    pass
