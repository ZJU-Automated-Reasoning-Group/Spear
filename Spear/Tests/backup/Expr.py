# Constant: int, str, float, 
# Unary Op, Binary Op: int, str, list
# ifexpr
# namedexpr

a = 1
b = 2.2
c = [3, "4"] if (a := 6) + b > 7 else ({8, 9}, {10: None})
d = e = c[0]
