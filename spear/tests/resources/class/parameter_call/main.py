class C:
    def func3(self):
        pass

    def func2(self, a):
        a()

    def func1(self, a, b):
        a(b)


a = C()
a.func1(a.func2, a.func3)
