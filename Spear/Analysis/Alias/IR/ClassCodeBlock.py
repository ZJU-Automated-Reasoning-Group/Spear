from typing import Set

from Spear.Analysis.Alias.IR.CodeBlock import CodeBlock
from Spear.Analysis.Alias.IR.IRStmts import Variable


class ClassCodeBlock(CodeBlock):
    thisClassVariable: Variable  # refer to $thisClass
    declaredGlobal: Set[str]  # a list of names declared global
    attributes: Set[str]

    def __init__(self, name: str, enclosing: 'CodeBlock', id: int, fake=False):
        super().__init__(name, enclosing, fake=False)
        self.id = f"{enclosing.id}.${id}"
        self.module = enclosing.module
        self.thisClassVariable = Variable("$thisClass", self)
        self.scopeLevel = enclosing.scopeLevel
