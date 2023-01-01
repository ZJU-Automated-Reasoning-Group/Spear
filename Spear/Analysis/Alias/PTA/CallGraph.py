from collections import defaultdict
from typing import Dict, List, Set

from Spear.Analysis.Alias.IR.CodeBlock import CodeBlock
from Spear.Analysis.Alias.IR.IRStmts import IRStmt


class CallGraph:

    # reachable: Set[CodeBlock]
    def __init__(self):
        self.callgraph = defaultdict(set)

    def put(self, stmt: IRStmt, code_block: CodeBlock) -> bool:
        # assert(isinstance(stmt, NewModule) and isinstance(codeBlock, ModuleCodeBlock) or
        #        isinstance(stmt, NewClass) and isinstance(codeBlock, ClassCodeBlock) or
        #        isinstance(stmt, Call) and isinstance(codeBlock, FunctionCodeBlock))

        if code_block not in self.callgraph[stmt]:
            self.callgraph[stmt].add(code_block)
            return True
        else:
            return False

    def get(self, stmt: IRStmt) -> Set:

        return self.callgraph[stmt]

    def dump(self, fp) -> Dict[CodeBlock, Dict[IRStmt, Set[CodeBlock]]]:
        callgraph = self.foldToStmt()
        for caller, map in callgraph.items():

            print(caller.readable_name + ":", file=fp)
            for stmt, callees in map.items():
                head = f"{stmt} -> "
                w = len(head)

                for callee in callees:
                    print(f"{head:<{w}}{callee.readable_name}", file=fp)
                    head = ""

            print("", file=fp)

        # return a dict of callgraph, formed with str

    def export(self) -> Dict[str, List[str]]:
        tmp = self.foldToCodeBlock()
        callgraph = {}
        for caller, callees in tmp.items():
            callgraph[caller.readable_name] = [callee.readable_name for callee in callees if not callee.fake]

        return callgraph

    def foldToStmt(self) -> Dict[CodeBlock, Dict[IRStmt, Set[CodeBlock]]]:
        callgraph = defaultdict(dict)
        for stmt, callees in self.callgraph.items():
            caller = stmt.belongsTo
            callgraph[caller][stmt] = callees
        return callgraph

    def foldToCodeBlock(self) -> Dict[CodeBlock, Set[CodeBlock]]:
        callgraph = defaultdict(set)
        for stmt, callees in self.callgraph.items():
            caller = stmt.belongsTo
            callgraph[caller] |= callees
        return callgraph
