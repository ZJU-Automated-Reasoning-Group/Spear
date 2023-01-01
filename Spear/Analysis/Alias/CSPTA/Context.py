import typing
from typing import Tuple

if typing.TYPE_CHECKING:
    from Spear.Analysis.Alias.CSPTA import CSStmt
    from Spear.Analysis.Alias.CSPTA.CSObjects import CSObject

from Spear.Analysis.Alias.IR.IRStmts import IRStmt

CTX_LENGTH = 1


# 2-callsite
class ContextElement:
    key: IRStmt

    def __init__(self, key):
        self.key = key

    def __eq__(self, other):
        return isinstance(other, ContextElement) and self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def __str__(self):
        return f"{self.key.belongsTo.readable_name}-{self.key.belongsTo.stmts.index(self.key)}"


# Context consists of ContextElement, the newest are placed at the end, the first which is ctx[0] is the oldest
# when context is full, the first element is dropped
Context = Tuple[ContextElement, ...]

# Context Chains consist of contexts, whose numbers are the same as codeblocks' scopeLevel, and therefore are not fixed.
# The first context is the outermost function's, 
ContextChain = Tuple[Context, ...]


def emptyContextChain():
    return ()


# callsite
def selectContext(cs_callsite: 'CSStmt', self_obj: 'CSObject') -> Context:
    # return selectCallSiteContext(csCallSite, selfObj)
    return selectMixedContext(cs_callsite, self_obj)


def selectCallSiteContext(cs_callsite: 'CSStmt', self_obj: 'CSObject') -> Context:
    ctx, callsite = cs_callsite
    if len(ctx) == 0:
        tail = [None] * CTX_LENGTH
        tail = *tail,
    else:
        tail = ctx[-1]
    return *tail[1:], ContextElement(callsite)


def selectObjectContext(cs_callsite: 'CSStmt', self_obj: 'CSObject') -> Context:
    if self_obj is None:
        ctx, callsite = cs_callsite
        if len(ctx) == 0:
            tail = [None] * CTX_LENGTH
            tail = *tail,
        else:
            tail = ctx[-1]
        return tail
    else:
        ctx, alloc_site = self_obj.ctxChain, self_obj.alloc_site
        if len(ctx) == 0:
            tail = [None] * CTX_LENGTH
            tail = *tail,
        else:
            tail = ctx[-1]
        return *tail[1:], ContextElement(alloc_site)


def selectMixedContext(cs_callsite: 'CSStmt', self_obj: 'CSObject') -> Context:
    if self_obj:
        return selectObjectContext(cs_callsite, self_obj)
    else:
        return selectCallSiteContext(cs_callsite, self_obj)
