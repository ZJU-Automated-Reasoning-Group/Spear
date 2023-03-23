import ast
from typing import Set


class DeclarationScanner(ast.NodeVisitor):
    declaredGlobal: Set[str]
    declaredNonlocal: Set[str]

    # nodes under module, function, class is not considered
    def __init__(self):
        self.declaredGlobal = set()
        self.declaredNonlocal = set()

    def visit_Module(self, node: ast.Module) -> None:
        pass

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        pass

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        pass

    def visit_Global(self, node: ast.Global) -> None:
        self.declaredGlobal |= set(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.declaredNonlocal |= set(node.names)
