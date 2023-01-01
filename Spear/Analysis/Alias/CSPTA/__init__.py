from typing import Tuple, Union

from Spear.Analysis.Alias.CSPTA.Context import ContextChain
from Spear.Analysis.Alias.IR.CodeBlock import CodeBlock
from Spear.Analysis.Alias.IR.IRStmts import Assign, Call, DelAttr, GetAttr, IRStmt, NewBuiltin, NewClass, NewFunction, NewModule, \
    NewStaticMethod, NewSuper, SetAttr, NewClassMethod

CSStmt = Tuple[ContextChain, IRStmt]
Stmt = Union[IRStmt, CSStmt]
CSCodeBlock = Tuple[ContextChain, CodeBlock]
CS_Assgin = Tuple[ContextChain, Assign]
CS_SetAttr = Tuple[ContextChain, SetAttr]
CS_GetAttr = Tuple[ContextChain, GetAttr]
CS_DelAttr = Tuple[ContextChain, DelAttr]
CS_NewModule = Tuple[ContextChain, NewModule]
CS_NewClass = Tuple[ContextChain, NewClass]
CS_NewFunction = Tuple[ContextChain, NewFunction]
CS_NewBuiltin = Tuple[ContextChain, NewBuiltin]
CS_Call = Tuple[ContextChain, Call]
CS_NewClassMethod = Tuple[ContextChain, NewClassMethod]
CS_NewStaticMethod = Tuple[ContextChain, NewStaticMethod]
CS_NewSuper = Tuple[ContextChain, NewSuper]
