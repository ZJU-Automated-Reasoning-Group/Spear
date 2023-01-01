class C:
    def foo(): pass


c = C()
c.foo = C.foo
del c.foo
del C.foo
