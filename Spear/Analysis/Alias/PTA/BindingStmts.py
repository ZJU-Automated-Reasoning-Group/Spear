from collections import defaultdict
from typing import Dict, Set, Tuple

from Spear.Analysis.Alias.PTA.Pointers import VarPtr
from Spear.Analysis.Alias.IR.IRStmts import IRStmt


class BindingStmts:
    bindings: Tuple[Dict[VarPtr, Set], ...]

    def __init__(self):
        opnames = [
            # "GetAttr",
            # "SetAttr",
            "NewClass",
            "Call",
            "DelAttr",
            "NewStaticMethod",
            # "NewClassMethod",
            "NewSuper"]
        self.bindings = {}
        for opname in opnames:
            self.bindings[opname] = defaultdict(set)

    def bind(self, opname, var_ptr: VarPtr, stmt_info: IRStmt):
        self.bindings[opname][var_ptr].add(stmt_info)

    def get(self, opname, var_ptr: VarPtr):
        return self.bindings[opname][var_ptr]
