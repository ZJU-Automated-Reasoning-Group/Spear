# list: subscript
# tuple: return tuple, tuple unpack, starred
# dict

def reverse(x, y, z):
    return z, y, x


t = x, y, z = reverse(1, 2, 3)  # x = 3, y = 2, z = 1
l = [e for e in t]  # l.$values = 1, 2, 3

t2 = (0, *l, 4)
e0 = t2[0]  # 0
e1 = t2[1]  # 1, 2, 3
e4 = t2[-1]  # 4

for elt in t2:  # elt = 0, 1, 2, 3, 4
    pass
