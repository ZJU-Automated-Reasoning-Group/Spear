from typing import Any, Dict, List, Set, Tuple

from Spear.Analysis.Alias.IR.CodeBlock import CodeBlock
from Spear.Analysis.Alias.IR.IRStmts import Assign, Call, GetAttr, IRStmt, New, NewClass, NewFunction, NewStaticMethod, \
    NewSuper, \
    SetAttr, Variable

DEFINED_ASSIGN = 0
DEFINED_NECY = 1
DEFINED_OTHERS = 2
USED_ASSIGN = 3
USED_OTHERS = 4

StmtInfo = Tuple[IRStmt, Any]


class Optimizer:
    codeBlocks: List[CodeBlock]
    tmpStmts: Dict[Variable, Tuple[Set[StmtInfo], ...]]
    workingList: List

    def __init__(self, code_blocks: List[CodeBlock]):
        self.codeBlocks = code_blocks
        self.tmpStmts = {}
        self.workingList = []

    def start(self):
        self.count()
        self.process()
        self.postprocess()

    def count(self):
        for codeBlock in self.codeBlocks:
            for stmt in codeBlock.stmts:
                self.operateStmt(stmt, self.add)

    # add an statement or delete a statement
    def operateStmt(self, stmt: IRStmt, operate):
        if isinstance(stmt, Assign):
            operate(stmt.source, (stmt, "source"), USED_ASSIGN)
            operate(stmt.target, (stmt, "target"), DEFINED_ASSIGN)
        elif isinstance(stmt, SetAttr):
            operate(stmt.source, (stmt, "source"), USED_OTHERS)
            operate(stmt.target, (stmt, "target"), USED_OTHERS)
        elif isinstance(stmt, GetAttr):
            operate(stmt.source, (stmt, "source"), USED_OTHERS)
            operate(stmt.target, (stmt, "target"), DEFINED_OTHERS)
        elif isinstance(stmt, New):
            if isinstance(stmt, NewClass) or isinstance(stmt, NewFunction):
                operate(stmt.target, (stmt, "target"), DEFINED_NECY)
            else:
                operate(stmt.target, (stmt, "target"), DEFINED_OTHERS)

            if isinstance(stmt, NewClass):
                for i in range(len(stmt.bases)):
                    base = stmt.bases[i]
                    operate(base, (stmt, i), USED_OTHERS)
            elif isinstance(stmt, NewStaticMethod):
                operate(stmt.func, (stmt, "func"), USED_OTHERS)
            elif isinstance(stmt, NewSuper):
                operate(stmt.type, (stmt, "type"), USED_OTHERS)
                operate(stmt.bound, (stmt, "bound"), USED_OTHERS)
        elif isinstance(stmt, Call):
            operate(stmt.target, (stmt, "target"), DEFINED_NECY)
            operate(stmt.callee, (stmt, "callee"), USED_OTHERS)
            for i in range(len(stmt.posargs)):
                arg = stmt.posargs[i]
                operate(arg, (stmt, i), USED_OTHERS)
            for kw, arg in stmt.kwargs.items():
                operate(arg, (stmt, f"kw_{kw}"), USED_OTHERS)

    def add(self, tmp_var: Variable, stmt_info: StmtInfo, type: int) -> bool:
        if not tmp_var.isTmp:
            return False
        if tmp_var not in self.tmpStmts:
            self.tmpStmts[tmp_var] = (set(), set(), set(), set(), set())
        self.tmpStmts[tmp_var][type].add(stmt_info)
        return True

    def remove(self, tmp_var, stmt_info, type: int):
        if (not tmp_var.isTmp or
                tmp_var not in self.tmpStmts or
                stmt_info not in self.tmpStmts[tmp_var][type]):
            return False
        self.tmpStmts[tmp_var][type].remove(stmt_info)
        self.workingList.append(tmp_var)
        return True

    def replace(self, stmt_info, new_var):
        stmt, arg = stmt_info
        if arg == "target":
            stmt.target = new_var
            if isinstance(stmt, Assign):
                type = DEFINED_ASSIGN
            elif isinstance(stmt, NewClass) or isinstance(stmt, NewFunction) or isinstance(stmt, Call):
                type = DEFINED_NECY
            elif isinstance(stmt, SetAttr):
                type = USED_OTHERS
            else:
                type = DEFINED_OTHERS
        elif arg == "source":
            stmt.source = new_var
            if isinstance(stmt, Assign):
                type = USED_ASSIGN
            else:
                type = USED_OTHERS
        else:
            type = USED_OTHERS
            if arg == "func":
                stmt.func = new_var
            elif arg == "type":
                stmt.type = new_var
            elif arg == "bound":
                stmt.bound = new_var
            elif arg == "callee":
                stmt.callee = new_var
            elif isinstance(arg, int):
                if isinstance(stmt, NewClass):
                    stmt.bases[arg] = new_var
                elif isinstance(stmt, Call):
                    stmt.posargs[arg] = new_var
            elif isinstance(arg, str) and arg.startswith("kw_"):
                kw = arg[3:]
                stmt.kwargs[kw] = new_var

        self.add(new_var, stmt_info, type)

    def process(self):
        self.workingList = list(self.tmpStmts.keys())
        while self.workingList:
            tmp_var = self.workingList[0]
            del self.workingList[0]

            if tmp_var not in self.tmpStmts:
                continue

            da, dn, do, ua, uo = self.tmpStmts[tmp_var]
            # Situation 1: Not Used, except Call, NewFunction, NewClass
            if len(ua) == 0 and len(uo) == 0 and len(dn) == 0:
                for stmtInfo in da | do:
                    stmt, arg = stmtInfo
                    self.operateStmt(stmt, self.remove)
                    stmt.belongsTo.removeIR(stmt)
                del self.tmpStmts[tmp_var]

            # Situation 2: Used Once
            elif len(ua) == 1 and len(uo) == 0:
                stmt, arg = next(iter(ua))
                assert (isinstance(stmt, Assign))
                new_var = stmt.target
                for stmtInfo in da | dn | do:
                    self.replace(stmtInfo, new_var)
                self.operateStmt(stmt, self.remove)
                stmt.belongsTo.removeIR(stmt)
                del self.tmpStmts[tmp_var]

            # Situation 3: Defined Once
            elif len(da) == 1 and len(dn) == 0 and len(do) == 0:
                stmt, arg = next(iter(da))
                assert (isinstance(stmt, Assign))
                new_var = stmt.source
                for stmtInfo in ua | uo:
                    self.replace(stmtInfo, new_var)
                self.operateStmt(stmt, self.remove)
                stmt.belongsTo.removeIR(stmt)
                del self.tmpStmts[tmp_var]

    def postprocess(self):
        pass
