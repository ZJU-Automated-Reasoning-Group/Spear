import ast
import typing
from typing import Any, Set

from spear.analysis.alias.ir_generation.binding_scanner import BindingScanner
from spear.analysis.alias.ir_generation.code_generator import Attribute, CodeBlockGenerator
from spear.analysis.alias.ir_generation.declaration_scanner import DeclarationScanner
from spear.analysis.alias.ir.class_code_block import ClassCodeBlock
from spear.analysis.alias.ir.function_code_block import FunctionCodeBlock
from spear.analysis.alias.ir.ir_stmts import Variable

if typing.TYPE_CHECKING:
    from spear.analysis.alias.module_manager import ModuleManager


class FunctionGenerator(CodeBlockGenerator):
    codeBlock: FunctionCodeBlock
    yielded: Set[Variable]
    sended: Variable

    def __init__(self, code_block: FunctionCodeBlock, module_manager: 'ModuleManager'):

        super().__init__(module_manager)
        self.codeBlock = code_block
        self.yielded = set()
        self.sended = Variable("$sended", self.codeBlock)

    def parse(self, node: ast.AST):
        assert (isinstance(node, ast.FunctionDef) or isinstance(node, ast.Lambda) or isinstance(node,
                                                                                                ast.AsyncFunctionDef))
        return super().parse(node)

    def preprocess(self, node):
        # get all locals, including args, function defintion, class Definition
        # remember global and nonlocal
        super().preprocess(node)
        code_block = self.codeBlock

        if isinstance(node, ast.Lambda):
            node.body = [node.body]

        ds = DeclarationScanner()

        for stmt in node.body:
            ds.visit(stmt)

        code_block.declaredGlobal = ds.declaredGlobal
        declared_names = ds.declaredGlobal | ds.declaredNonlocal

        ls = BindingScanner(declared_names)
        for stmt in node.body:
            ls.visit(stmt)
        for name in ls.boundNames:
            v = Variable(name, code_block)
            code_block.localVariables[name] = v

        # args are also local names, not affected by "global" and "nonlocal"
        # for assignment can't be earlier than declarations
        args = node.args

        # posonlyargs
        for arg in args.posonlyargs:
            v = Variable(arg.arg, code_block)
            code_block.posargs.append(v)
            code_block.localVariables[arg.arg] = v
        # args

        for arg in args.args:
            v = Variable(arg.arg, code_block)
            code_block.posargs.append(v)
            code_block.kwargs[arg.arg] = v
            code_block.localVariables[arg.arg] = v

        # kwonlyargs
        for arg in args.kwonlyargs:
            v = Variable(arg.arg, code_block)
            code_block.kwargs[arg.arg] = v
            code_block.localVariables[arg.arg] = v

        if args.vararg:
            v = Variable(args.vararg.arg, code_block)
            # varargs are passed into this list (referenced by tmp)
            # then v points to this list, remember v can point other object
            # this approach can avoid varargs to spread to other object
            vararg = self.newTmpVariable()
            self.addNewBuiltin(vararg, "list")
            tmp = self.newTmpVariable()
            self.addSetAttr(Attribute(vararg, "$values"), tmp)
            self.addAssign(v, vararg)

            code_block.vararg = tmp
            code_block.localVariables[args.vararg.arg] = v

        if args.kwarg:
            v = Variable(args.kwarg.arg, code_block)
            kwarg = self._makeDict()
            tmp = self.newTmpVariable()
            code_block.kwarg = tmp
            self.addSetAttr(Attribute(kwarg, "$values"), tmp)
            self.addAssign(v, kwarg)
            code_block.localVariables[args.kwarg.arg] = v

        if (isinstance(code_block.enclosing, ClassCodeBlock)
                and isinstance(node, ast.FunctionDef) and len(code_block.posargs) > 0):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == "staticmethod":
                    break
            else:
                enclosing_class = code_block.enclosing
                self.addAssign(code_block.posargs[0], enclosing_class.thisClassVariable)

    def postprocess(self, node: ast.AST):

        if self.yielded:

            # tmp = self._makeGenerator(self.yielded, self.sended)
            tmp = self.newTmpVariable()
            self.addNewBuiltin(tmp, "list")
            for yielded in self.yielded:
                self.addSetAttr(Attribute(tmp, "$values"), yielded)
            self.addAssign(self.codeBlock.returnVariable, tmp)

        super().postprocess(node)

    def visit_Return(self, node: ast.Return) -> Any:

        self.generic_visit(node)
        if node.value:
            self.addAssign(self.codeBlock.returnVariable, node.value.result)

    def visit_Yield(self, node: ast.Yield) -> Any:

        self.generic_visit(node)
        if node.value:
            self.yielded.add(node.value.result)
        # else:
        #     self.yielded.add(None)
        # node.result = self.sended

    def visit_YieldFrom(self, node: ast.YieldFrom) -> Any:

        self.generic_visit(node)
        tmp = self.newTmpVariable()
        self.addGetAttr(tmp, Attribute(node.value.result, "$values"))

        self.yielded.add(tmp)
        # node.result = self.sended
