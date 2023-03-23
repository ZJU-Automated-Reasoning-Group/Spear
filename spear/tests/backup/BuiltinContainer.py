# build List, Tuple, Dict
# slice
# List, Tuple assign
# List, Tuple return

def foo(x, y, z):
    sum = x + y + z
    return x / sum, y / sum, z / sum, sum


t = []
t[0:2] = a, *b, c = foo(1, 2, 3)
dup = *b, *b
d = {i: i + 1 for i in t}
