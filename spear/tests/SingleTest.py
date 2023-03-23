import json
import os
import shutil

from spear.analysis.alias.ModuleManager import ModuleManager
from spear.analysis.alias import json_utils
from spear.analysis.alias.pta import Analysis


def testScript(path, filename):
    resource = os.path.join(os.path.dirname(__file__), "resources")
    # with open(os.path.join(resource, path), "r") as f:
    #     print(ast.dump(ast.parse(f.read()), indent=4))

    module_manager = ModuleManager(os.path.join(resource, path))
    module_manager.addEntry(file=filename)
    test(module_manager)


def testModule(module_name, cwd):
    module_manager = ModuleManager(cwd, max_depth=0, verbose=True)
    module_manager.addEntry(module=module_name)
    test(module_manager)


def test(module_manager: ModuleManager):
    entrys = module_manager.getEntrys()
    result = os.path.join(os.path.dirname(__file__), "result")
    if os.path.exists(result):
        shutil.rmtree(result)
    os.mkdir(result)
    for cb in module_manager.allCodeBlocks():
        cb.dump(result)

    print("IR generation finish, start PTA...                      ")

    analysis = Analysis(verbose=True)
    analysis.analyze(entrys)

    with open(os.path.join(result, "Point-To Set.json"), "w") as f:
        f.write(analysis.pointToSet.to_json())

    with open(os.path.join(result, "CallGraph.json"), "w") as f:
        json.dump(analysis.callgraph, f, default=json_utils.default, indent=4)

    with open(os.path.join(result, "Pointer Flow.json"), "w") as f:
        f.write(analysis.pointerFlow.to_json())

    with open(os.path.join(result, "Class Hiearchy.json"), "w") as f:
        f.write(analysis.classHiearchy.to_json())

    # print("Done                                                   ")
testScript("call/assigned_call", "main.py")
# testModule("flask", ".../flask/src")
