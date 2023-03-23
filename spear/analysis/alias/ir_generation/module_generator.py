import ast
import typing

from spear.analysis.alias.ir_generation.code_generator import CodeBlockGenerator
from spear.analysis.alias.ir.ModuleCodeBlock import ModuleCodeBlock

if typing.TYPE_CHECKING:
    from spear.analysis.alias.ModuleManager import ModuleManager

# builtin_names = list(builtins.__dict__.keys())
builtin_names = ["object"]


class ModuleGenerator(CodeBlockGenerator):
    codeBlock: ModuleCodeBlock

    # module has no enclosing block
    def __init__(self, code_block: ModuleCodeBlock, module_manager: 'ModuleManager'):
        super().__init__(module_manager)
        self.codeBlock = code_block

    def preprocess(self, node: ast.Module):
        node.body.append(
            ast.ImportFrom(module="builtins", names=[ast.alias(name=name) for name in builtin_names], level=0))

    def parse(self, node: ast.AST):
        assert (isinstance(node, ast.Module))
        return super().parse(node)
