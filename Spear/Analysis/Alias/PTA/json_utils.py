from Spear.Analysis.Alias.PTA.Objects import Object
from Spear.Analysis.Alias.PTA.Pointers import Pointer


def default(o):
    if isinstance(o, set):
        return list(o)
    elif isinstance(o, Object) or isinstance(o, Pointer):
        return str(o)
    else:
        raise Exception(f"Type {type(o).__name} not supported.")
