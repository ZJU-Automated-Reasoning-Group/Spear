import ast
from typing import Set


# If a name binding operation occurs Nonewhere within a code block,
# all uses of the name within the block are treated as references to the current block.
# See https://docs.python.org/3.9/reference/executionmodel.html
class BindingScanner(ast.NodeVisitor):
    declaredNames: Set[str]
    boundNames: Set[str]

    def __init__(self, declared_names):
        self.declaredNames = declared_names
        self.boundNames = set()

    def visit_Module(self, node: ast.Module) -> None:
        pass

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name not in self.declaredNames:
            self.boundNames.add(node.name)
        # no generic visit

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.name not in self.declaredNames:
            self.boundNames.add(node.name)
        # no generic visit

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.asname is None:
                name, _, _ = alias.name.partition(".")
            else:
                name = alias.asname

            if name not in self.declaredNames:
                self.boundNames.add(name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.asname is None and alias.name not in self.declaredNames:
                self.boundNames.add(alias.name)
            elif alias.asname is not None and alias.asname not in self.declaredNames:
                self.boundNames.add(alias.asname)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store) and node.id not in self.declaredNames:
            self.boundNames.add(node.id)
