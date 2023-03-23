from typing import Set

from spear.analysis.alias.ir.code_block import CodeBlock
from spear.analysis.alias.ir.ir_stmts import Variable


class ModuleCodeBlock(CodeBlock):
    globalNames: Set[str]
    globalVariable: Variable  # $global, all code blocks in a module share a single $global variable

    def __init__(self, name: str, fake=False):
        super().__init__(name, None, fake)
        self.id = self.readable_name  # Module's id = qualified name, cause I don't think there are duplicate modules
        self.module = self
        self.globalVariable = Variable("$global", self)
        # self.done = False
        self.globalNames = set()
        self.scopeLevel = 0
