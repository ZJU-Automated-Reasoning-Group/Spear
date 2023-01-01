class C:
    def func(self):
        def nested():
            pass

        nested()


a = C()
a.func()
