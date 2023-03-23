from typing import Set

from spear.analysis.alias.ir.code_block import CodeBlock
from spear.analysis.alias.ir.ir_stmts import Variable


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
