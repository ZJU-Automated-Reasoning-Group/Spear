from spear.analysis.alias.pta.Objects import BuiltinObject, ClassMethodObject, ClassObject, FakeObject, \
    FunctionObject, ModuleObject, StaticMethodObject, SuperObject

OBJ_MODULE = 0
OBJ_CLASS = 1
OBJ_FUNCTION = 2
OBJ_BUILTIN = 3
OBJ_STATIC_METHOD = 4
OBJ_CLASS_METHOD = 5
OBJ_SUPER = 6
OBJ_FAKE = 7
OBJ_TYPE_NUM = 8


class ObjectPool:

    def __init__(self):
        self.pool = {}

    def create(self, type: int, *vararg, **kwarg):
        if type == OBJ_MODULE:
            return self._create(ModuleObject, *vararg, **kwarg)
        elif type == OBJ_CLASS:
            return self._create(ClassObject, *vararg, **kwarg)
        elif type == OBJ_FUNCTION:
            return self._create(FunctionObject, *vararg, **kwarg)
        elif type == OBJ_BUILTIN:
            return self._create(BuiltinObject, *vararg, **kwarg)
        elif type == OBJ_STATIC_METHOD:
            return self._create(StaticMethodObject, *vararg, **kwarg)
        elif type == OBJ_CLASS_METHOD:
            return self._create(ClassMethodObject, *vararg, **kwarg)
        elif type == OBJ_SUPER:
            return self._create(SuperObject, *vararg, **kwarg)
        elif type == OBJ_FAKE:
            return self._create(FakeObject, *vararg, **kwarg)

    def _create(self, obj_cls, *vararg, **kwarg):
        id = obj_cls.generateID(*vararg, **kwarg)
        if id in self.pool:
            return self.pool[id]
        else:
            obj = obj_cls.create(*vararg, **kwarg)
            self.pool[id] = obj
            return obj

    def get(self, id):
        if id in self.pool:
            return self.pool[id]
