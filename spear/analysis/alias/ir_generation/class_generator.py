"""
This module contains the ClassGenerator class, which is responsible for generating IR code for a Python class definition.
"""

import ast
from typing import Set
import typing

from spear.analysis.alias.ir.ir_stmts import Variable
from spear.analysis.alias.ir.class_code_block import ClassCodeBlock

from spear.analysis.alias.ir_generation.declaration_scanner import DeclarationScanner
from spear.analysis.alias.ir_generation.binding_scanner import BindingScanner

from spear.analysis.alias.ir_generation.code_generator import Attribute, CodeBlockGenerator, \
    isLoad, isStore, resolveName

if typing.TYPE_CHECKING:
    from ..module_manager import ModuleManager


class ClassGenerator(CodeBlockGenerator):
    codeBlock: ClassCodeBlock
    attributes: Set[str]

    def __init__(self, code_block, module_manager: 'ModuleManager'):
        super().__init__(module_manager)
        self.codeBlock = code_block

    def parse(self, node: ast.AST):
        assert (isinstance(node, ast.ClassDef))
        return super().parse(node)

    def preprocess(self, node: ast.ClassDef):
        super().preprocess(node)
        ds = DeclarationScanner()
        for stmt in node.body:
            ds.visit(stmt)

        self.codeBlock.declaredGlobal = ds.declaredGlobal
        declared_names = ds.declaredGlobal | ds.declaredNonlocal

        ls = BindingScanner(declared_names)
        for stmt in node.body:
            ls.visit(stmt)
        self.codeBlock.attributes = ls.boundNames

    # for name loaded, because our analysis is flow-insensitive,
    # we can't tell if this name is loaded before its first assignment.
    # we make conservative guesses, and suggest that this name may
    # be resolved to a variable/attribute outside, or an attribute of this class
    def visit_Name(self, node: ast.Name):
        id = node.id
        code_block = self.codeBlock
        if isLoad(node):
            # an varaible/attribute outside, or this class's attribute

            if id in code_block.attributes:
                outside = resolveName(code_block.enclosing, id)
                tmp = self.newTmpVariable()
                # $tmp = $thisClass.attr
                self.addGetAttr(tmp, Attribute(code_block.thisClassVariable, id))

                if isinstance(outside, Variable):
                    # $tmp = v
                    self.addAssign(tmp, outside)
                elif isinstance(outside, Attribute):
                    self.addGetAttr(tmp, outside)
                node.result = tmp
            else:
                outside = resolveName(code_block, id)
                if isinstance(outside, Attribute):
                    # this name is not one of this class's attributes, the name resolved to a global variable
                    tmp = self.newTmpVariable()
                    self.addGetAttr(tmp, outside)
                    node.result = tmp
                else:
                    # this name is not one of this class's attributes, the name resolved to a local variable
                    node.result = outside

        elif isStore(node):
            # return this class's attribute if it is
            node.result = resolveName(code_block, id)
