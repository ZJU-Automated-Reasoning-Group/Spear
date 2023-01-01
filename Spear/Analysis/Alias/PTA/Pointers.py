import typing

if typing.TYPE_CHECKING:
    from Spear.Analysis.Alias.PTA.Objects import Object
from Spear.Analysis.Alias.IR.IRStmts import Variable


class Pointer:
    id: str

    def __repr__(self) -> str:
        return f"VarPtr: {self.id}"

    def __eq__(self, other):
        return isinstance(other, Pointer) and self.id == other.id

    def __str__(self):
        return self.readable_name if hasattr(self, 'readable_name') else self.id

    def __hash__(self):
        return hash(self.id)


class VarPtr(Pointer):

    def __init__(self, id: str, readable_name: str):
        self.id = id
        self.readable_name = readable_name

    @staticmethod
    def create(var: Variable):
        return VarPtr(var.id, var.readable_name)


class AttrPtr(Pointer):
    obj: 'Object'
    attr: str

    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr
        self.id = f"<{obj.id}>.{attr}"
        if hasattr(obj, "readable_name"):
            self.readable_name = f"<{obj.readable_name}>.{attr}"
