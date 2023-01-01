from typing import Dict, List, Set

from Spear.Analysis.Alias.IR.CodeBlock import CodeBlock
from Spear.Analysis.Alias.IR.IRStmts import Variable


class FunctionCodeBlock(CodeBlock):
    scopeLevel: int  # showing how deep a function is defined, startging with 0
    localVariables: Dict[str, Variable]  # a map from name to variable

    # posargs and kwargs both store all the arguments
    # using two data structure is for convenience 

    posargs: List[Variable]
    kwargs: Dict[str, Variable]
    vararg: Variable
    kwarg: Variable

    declaredGlobal: Set[str]  # a list of names declared global
    returnVariable: Variable

    def __init__(self, name: str, enclosing: 'CodeBlock', id: int, fake=False):
        super().__init__(name, enclosing, fake)
        self.id = f"{enclosing.id}.${id}"
        # function's id != qualified name, cause there may be functions sharing the same name.
        self.module = enclosing.module
        self.localVariables = {}
        self.declaredGlobal = set()
        # self.posonlyargs = []
        self.posargs = []
        self.kwargs = {}
        # self.kwonlyargs = {}
        self.vararg = None
        self.kwarg = None
        self.returnVariable = Variable("$ret", self)
        self.scopeLevel = enclosing.scopeLevel + 1
