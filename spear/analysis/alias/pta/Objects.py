from typing import List, Tuple, Union

from spear.analysis.alias.pta.Pointers import VarPtr
from spear.analysis.alias.ir.function_code_block import FunctionCodeBlock
from spear.analysis.alias.ir.ir_stmts import NewBuiltin, NewClass, NewFunction
from spear.analysis.alias.ir.ModuleCodeBlock import ModuleCodeBlock


# Object's information should remain static as the pta proceeds.
# Objects have loose relation with IR, but contain all the necessary information in the IR, and can be easily exported. 
# That means even without IR, objects can be still represented, and pta can still run. 

class Object:
    id: str

    def __init__(self, obj_type: str):
        self.objType = obj_type

    def __str__(self):
        return self.readable_name if hasattr(self, 'readable_name') else self.id

    def __eq__(self, other):
        return isinstance(other, Object) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return self.id


class ModuleObject(Object):
    # codeBlock: ModuleCodeBlock
    readable_name: str

    def __init__(self, id: str, readable_name: str):
        super().__init__("Module")
        self.id = id
        self.readable_name = readable_name

    @staticmethod
    def create(module: ModuleCodeBlock):
        return ModuleObject(id=ModuleObject.generateID(module),
                            readable_name=module.readable_name)

    @staticmethod
    def generateID(module: ModuleCodeBlock):
        return f"Module({module.id})"

    def unwrapID(self):
        return self.id[7:-1]


class FunctionObject(Object):
    codeBlock: FunctionCodeBlock  # used

    # necessary info in IR
    readable_name: str
    codeBlock: FunctionCodeBlock
    retVar: VarPtr
    posParams: List[VarPtr]
    kwParams: List[VarPtr]
    varParam: VarPtr
    kwParam: VarPtr

    def __init__(self, id: str,
                 readable_name: str,
                 code_block: FunctionCodeBlock,
                 ret_var: VarPtr,
                 pos_params: List[VarPtr],
                 kw_params: List[VarPtr],
                 var_param: VarPtr,
                 kw_param: VarPtr):
        super().__init__("Function")
        self.id = id
        self.readable_name = readable_name
        self.codeBlock = code_block
        self.retVar = ret_var
        self.posParams = pos_params
        self.kwParams = kw_params
        self.varParam = var_param
        self.kwParam = kw_param

    @staticmethod
    def create(alloc_site: NewFunction):
        func = alloc_site.codeBlock
        return FunctionObject(id=FunctionObject.generateID(alloc_site),
                              readable_name=func.readable_name,
                              code_block=func,
                              ret_var=VarPtr.create(func.returnVariable),
                              pos_params=[VarPtr.create(posarg) for posarg in func.posargs],
                              kw_params={kw: VarPtr.create(kwOnlyParam) for kw, kwOnlyParam in func.kwargs.items()},
                              var_param=VarPtr.create(func.vararg) if func.vararg else None,
                              kw_param=VarPtr.create(func.kwarg) if func.kwarg else None
                              )

    @staticmethod
    def generateID(alloc_site: NewFunction):
        return f"Function({alloc_site.codeBlock.id})"

    def unwrapID(self):
        return self.id[9:-1]


class ClassObject(Object):
    # alloc_site: NewClass
    readable_name: str
    bases: List[VarPtr]
    attributes: List[str]

    def __init__(self, id: str,
                 readable_name: str,
                 bases: List[VarPtr],
                 attributes: List[str]):
        super().__init__("Class")

        self.id = id
        self.readable_name = readable_name
        self.bases = bases
        self.attributes = attributes

    @staticmethod
    def generateID(alloc_site: NewClass):
        return f"Class({alloc_site.codeBlock.id})"

    @staticmethod
    def create(alloc_site: NewClass):
        code_block = alloc_site.codeBlock
        return ClassObject(id=ClassObject.generateID(alloc_site),
                           readable_name=code_block.readable_name,
                           bases=[VarPtr.create(base) for base in alloc_site.bases],
                           attributes=code_block.attributes)

    def unwrapID(self):
        return self.id[6:-1]


# class ConstObject(Object):
#     value: Any
#     def __eq__(self, other):
#         return isinstance(other, ConstObject) and self.value == other.value
#     def __hash__(self):
#         return hash(self.value)
#     def __init__(self, value):
#         self.value = value
#     def __str__(self):
#         return f"Const({self.value})"
#     def __repr__(self):
#         return self.__str__()


class InstanceObject(Object):
    type: ClassObject

    def __eq__(self, other):
        return isinstance(other, InstanceObject) and self.type == other.type

    def __hash__(self):
        return hash(self.type)


# class CIObject(Object):
#     alloc_site: IRStmt
# def __eq__(self, other):
#     return isinstance(other, CIObject) and self.alloc_site == other.alloc_site
# def __hash__(self):
#     return hash(self.alloc_site)
# def __init__(self, alloc_site):
#     self.alloc_site = alloc_site


# class CIInstanceObject(CIObject, InstanceObject):
#     alloc_site: Call
#     type: ClassObject

#     def __hash__(self):
#         return CIObject.__hash__(self) ^ InstanceObject.__hash__(self)

#     def __eq__(self, other):
#         return CIObject.__eq__(self, other) and InstanceObject.__eq__(self, other)

#     def __init__(self, alloc_site, type):
#         self.alloc_site = alloc_site
#         self.type = type

#     def __str__(self):
#         cb = self.alloc_site.belongsTo
#         return f"Instance {self.type.getCodeBlock().readable_name}({cb.readable_name}-{cb.stmts.index(self.alloc_site)})"
#     def __repr__(self):
#         return self.__str__()


class BuiltinObject(Object):

    def __init__(self, id: str):
        self.id = id

    @staticmethod
    def generateID(alloc_site: NewBuiltin):
        return f"Builtin({alloc_site.belongsTo.id}.${alloc_site.id})"

    @staticmethod
    def create(alloc_site: NewBuiltin):
        return BuiltinObject(id=BuiltinObject.generateID(alloc_site))

    def unwrapID(self):
        return self.id[8:-1]


class InstanceMethodObject(Object):
    selfObj: InstanceObject
    func: FunctionObject

    def __eq__(self, other):
        return isinstance(other, InstanceMethodObject) and self.selfObj == other.selfObj and self.func == other.func

    def __hash__(self):
        return hash((self.selfObj, self.func))

    def __init__(self, self_obj, func):
        self.selfObj = self_obj
        self.func = func

    def __str__(self):
        return f"InstanceMethod(self: {self.selfObj}, {self.func})"

    def __repr__(self):
        return self.__str__()


class ClassMethodObject(Object):
    classObj: ClassObject
    func: FunctionObject

    def __init__(self, id: str, class_obj: ClassObject, func: FunctionObject):
        self.classObj = class_obj
        self.func = func
        self.id = id

    @staticmethod
    def generateID(class_obj: ClassObject, func: FunctionObject):
        return f"ClassMethod({class_obj.id},{func.id})"

    @staticmethod
    def create(class_obj: ClassObject, func: FunctionObject):
        return ClassMethodObject(id=ClassMethodObject.generateID(class_obj, func),
                                 class_obj=class_obj,
                                 func=func)

    def unwrapID(self):
        return self.id[12:-1]


class StaticMethodObject(Object):
    func: FunctionObject

    def __init__(self, id: str, func: FunctionObject):
        self.func = func
        self.id = id

    @staticmethod
    def generateID(func: FunctionObject):
        return f"StaticMethod({func.id})"

    @staticmethod
    def create(func: FunctionObject):
        return StaticMethodObject(id=StaticMethodObject.generateID(func),
                                  func=func)

    def unwrapID(self):
        return self.id[13:-1]


class SuperObject(Object):
    type: ClassObject
    bound: ClassObject

    def __init__(self, id: str, type: ClassObject, bound: ClassObject):
        self.type = type
        self.bound = bound
        self.id = id

    @staticmethod
    def generateID(type: ClassObject, bound: ClassObject):
        return f"Super({type.id},{bound.id})"

    @staticmethod
    def create(type: ClassObject, bound: ClassObject):
        return SuperObject(id=SuperObject.generateID(type, bound),
                           type=type,
                           bound=bound)

    def unwrapID(self):
        return self.id[6:-1]


class FakeObject(ModuleObject, ClassObject, FunctionObject):
    GetEdge = Tuple[VarPtr, VarPtr, str]

    id: str
    # codeBlock: CodeBlock
    prefix: 'FakeObject'
    getAttr: GetEdge

    def __init__(self, id: str, prefix: 'FakeObject', get_attr: GetEdge):
        self.id = id
        self.prefix = prefix
        self.getAttr = get_attr

        # disguise
        self.readable_name = self.unwrapID()
        self.codeBlock = None
        self.retVar = VarPtr(f"$ret@{id}", f"$ret@{self.readable_name}")
        self.posParams = []
        self.kwParams = {}
        self.varParam = VarPtr("$varParam@{id}", f"$varParam@{self.readable_name}")
        self.kwParam = VarPtr("$kwParam@{id}", f"$kwParam@{self.readable_name}")
        self.bases = []
        self.attributes = []

    @staticmethod
    def generateID(prefix: Union['FakeObject', str], get_attr: GetEdge = None):
        if isinstance(prefix, FakeObject):
            prefix = FakeObject.cut(prefix, get_attr)
            _, _, attr = get_attr
            return f"Fake({prefix.unwrapID()}.{attr})"
        elif isinstance(prefix, str):
            return f"Fake({prefix})"

    @staticmethod
    def create(prefix: Union['FakeObject', str], get_attr: GetEdge = None):
        id = FakeObject.generateID(prefix, get_attr)
        if isinstance(prefix, FakeObject):
            return FakeObject(id=id,
                              prefix=prefix,
                              get_attr=get_attr)
        elif isinstance(prefix, str):
            return FakeObject(id=id,
                              prefix=None,
                              get_attr=None)

    @staticmethod
    def cut(prefix: 'FakeObject', get_attr: GetEdge) -> 'FakeObject':
        fo = prefix
        while fo.getAttr:
            if fo.getAttr == get_attr:
                return fo.prefix
            fo = fo.prefix
        return prefix

    def unwrapID(self):
        return self.id[5:-1]
