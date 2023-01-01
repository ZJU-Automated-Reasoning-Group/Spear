import typing

if typing.TYPE_CHECKING:
    from Spear.Analysis.Alias.CSPTA.Context import ContextChain
from Spear.Analysis.Alias.IR.IRStmts import Variable
from Spear.Analysis.Alias.PTA.Pointers import VarPtr


class CSVarPtr(VarPtr):
    ctxChain: 'ContextChain'
    var: Variable

    def __init__(self, ctx_chain: 'ContextChain', var: Variable):
        self.ctxChain = ctx_chain[:var.belongsTo.scopeLevel]
        self.var = var

    def __eq__(self, other):
        return isinstance(other, CSVarPtr) and self.ctxChain == other.ctxChain and self.var == other.var

    def __hash__(self):
        return hash((self.ctxChain, self.var))

    def __str__(self):
        ctx_chain_str = ", ".join(["#".join([str(e) for e in ctx if e]) for ctx in self.ctxChain])

        return f"({ctx_chain_str}){self.var}"
