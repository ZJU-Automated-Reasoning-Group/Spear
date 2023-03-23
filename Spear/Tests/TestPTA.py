import json
import os
import unittest
from typing import Dict, List

from Spear.Analysis.Alias.IR.CodeBlock import CodeBlock
from Spear.Analysis.Alias.ModuleManager import ModuleManager
import Spear.Analysis.Alias.PTA.Analysis as PTA


def countAllStmts(code_blocks: List[CodeBlock]):
    sum = 0
    for codeBlock in code_blocks:
        sum += len(codeBlock.stmts)
    return sum


class TestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def assertEqual(self, first: Dict[str, list], second: Dict[str, List]) -> None:
        first = {k: list(v) for k, v in first.items() if v}
        second = {k: list(v) for k, v in second.items() if v}
        for v in first.values():
            v.sort()
        for v in second.values():
            v.sort()
        super().assertEqual(first, second)

    def _test(self, analysis_type, path: str):

        # get output
        module_manager = ModuleManager(path)
        module_manager.addEntry(file="main.py")

        module_manager.allCodeBlocks()
        # num0 = countAllStmts(codeBlocks)
        # optimizer = Optimizer(codeBlocks)
        # optimizer.start()
        # num1 = countAllStmts(codeBlocks)
        # print(f"optimize {num0} -> {num1}")

        entrys = module_manager.getEntrys()
        analysis = analysis_type()
        analysis.analyze(entrys)
        output = analysis.callgraph

        # get expected output
        expected_path = os.path.join(path, "callgraph.json")
        with open(expected_path, "r") as f:
            expected = json.load(f)

        self.assertEqual(output, expected)


if __name__ == "__main__":
    def getPTATest(path):
        return lambda self: self._test(PTA, path)

    resourcePath = os.path.join(os.path.dirname(__file__), "resources")
    tests = []
    for item in os.listdir(resourcePath):
        itemPath = os.path.join(resourcePath, item)

        if not os.path.isdir(itemPath):
            continue
        clsName = "".join([s.capitalize() for s in item.split("_")])
        attrs = {}
        for subitem in os.listdir(itemPath):
            subitem_path = os.path.join(itemPath, subitem)
            attrName = "test" + "".join([s.capitalize() for s in subitem.split("_")])
            if not os.path.isdir(subitem_path):
                continue
            attrs[attrName] = getPTATest(subitem_path)
        globals()[clsName] = type(clsName, (TestBase,), attrs)
    unittest.main(verbosity=2)
