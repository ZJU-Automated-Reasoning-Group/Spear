import json
from collections import defaultdict
from typing import Dict, Set

from Spear.Analysis.Alias.PTA import json_utils
from Spear.Analysis.Alias.PTA.Objects import Object
from Spear.Analysis.Alias.PTA.Pointers import AttrPtr, Pointer, VarPtr


class PointToSet:
    varPtrSet: Dict[VarPtr, Set]
    attrPtrSet: Dict[Object, Dict[str, Set]]

    def __init__(self):
        self.varPtrSet = defaultdict(set)
        self.attrPtrSet = defaultdict(lambda: defaultdict(set))

    def put(self, pointer: Pointer, obj: Object) -> bool:
        if isinstance(pointer, VarPtr):
            var = pointer
            if obj not in self.varPtrSet[var]:
                self.varPtrSet[var].add(obj)
                return True
            else:
                return False
        elif isinstance(pointer, AttrPtr):
            o = pointer.obj
            f = pointer.attr
            if obj not in self.attrPtrSet[o][f]:
                self.attrPtrSet[o][f].add(obj)
                return True
            else:
                return False

    def putAll(self, pointer: Pointer, objs: Set[Object]) -> Set[Object]:
        if isinstance(pointer, VarPtr):
            var = pointer

            diff = objs - self.varPtrSet[var]
            self.varPtrSet[var] |= diff
            return diff
        elif isinstance(pointer, AttrPtr):
            o = pointer.obj
            f = pointer.attr

            diff = objs - self.attrPtrSet[o][f]
            self.attrPtrSet[o][f] |= diff
            return diff

    def get(self, pointer: Pointer) -> Set[Object]:
        if isinstance(pointer, VarPtr):
            var = pointer
            return self.varPtrSet[var]

        elif isinstance(pointer, AttrPtr):
            o = pointer.obj
            f = pointer.attr
            return self.attrPtrSet[o][f]

    def getAllAttr(self, obj: Object):

        return self.attrPtrSet[obj].keys()

    def to_json(self):
        attr_ptr_set = {str(AttrPtr(obj, attr)): objs for obj, d in self.attrPtrSet.items() for attr, objs in d.items()}
        var_ptr_set = {str(varPtr): s for varPtr, s in self.varPtrSet.items()}
        return json.dumps(attr_ptr_set | var_ptr_set, default=json_utils.default, indent=4)
