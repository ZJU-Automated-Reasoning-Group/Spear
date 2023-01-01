from typing import Dict, Set

from Spear.Analysis.Alias.CSPTA import CSCodeBlock, CSStmt
from Spear.Analysis.Alias.IR.CodeBlock import CodeBlock
from Spear.Analysis.Alias.IR.IRStmts import IRStmt
from Spear.Analysis.Alias.PTA.CallGraph import CallGraph


class CSCallGraph(CallGraph):
    callgraph: Dict[CSStmt, Set[CSCodeBlock]]  # three kinds: NewClass, NewModule, Call

    def foldToStmt(self) -> Dict[CodeBlock, Dict[IRStmt, Set[CodeBlock]]]:
        callgraph = {}
        for csStmt, csCallees in self.callgraph.items():
            stmt = csStmt[1]
            caller = stmt.belongsTo
            if caller not in callgraph:
                callgraph[caller] = {}

            if stmt not in callgraph[caller]:
                callgraph[caller][stmt] = set()
            callgraph[caller][stmt] |= {callee for ctx, callee in csCallees}
        return callgraph

    def foldToCodeBlock(self) -> Dict[CodeBlock, Set[CodeBlock]]:
        callgraph = {}
        for csStmt, csCallees in self.callgraph.items():
            stmt = csStmt[1]
            caller = stmt.belongsTo
            if caller not in callgraph:
                callgraph[caller] = set()
            callgraph[caller] |= {callee for ctx, callee in csCallees}
        return callgraph
