class C:
    def __init__(self):
        self.func1()

    def func1(self):
        self.func2()

    def func2(self):
        pass


a = C()
