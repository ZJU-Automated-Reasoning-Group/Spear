import argparse
import json
import os

from Spear.Analysis.Alias.CSPTA.Analysis import CSAnalysis
from Spear.Analysis.Alias.ModuleManager import ModuleManager
from Spear.Analysis.Alias.PTA.Analysis import Analysis

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("path",
                           help="the path of working directory where scripts and modules are placed. "
                                "Scripts should be placed directly in this directory."
                           )
    argparser.add_argument("-a", "--all-files",
                           action="store_true",
                           default=False,
                           help="Add all scripts in PATH as entry points. Scripts are files that end "
                                "with \".py\"."
                           )
    argparser.add_argument("-f", "--files",
                           nargs="+",
                           help="Add scripts as entry points."
                           )
    argparser.add_argument("-m", "--modules",
                           nargs="+",
                           help="Add library modules as entry points. Just like how you run program "
                                "using \"python -m \"."
                           )
    argparser.add_argument("-cs", "--context-sensitive",
                           action="store_true",
                           default=False,
                           help="Enable context sensitive. It may cost longer time."
                           )
    argparser.add_argument("-o", "--output",
                           required=False,
                           help="The file path where output callgraph will be stored. The output format will be json."
                           )
    argparser.add_argument("-nd", "--no-dependency",
                           action="store_true",
                           default=False,
                           help="""If in script mode, only modules under the same directory as the entry point
                            will be included. If in module mode, only modules under current directory will be 
                            included."""
                           )
    argparser.add_argument("--include",
                           help="Specify a string, then output callgraph only contains callers that "
                                "start with this string."
                           )

    args = argparser.parse_args()

    if not args.files and not args.modules and not args.all_files:
        print("Error: No entry point is provided.")
        exit()

    # mm = ModuleManager(args.path, verbose=True, dependency=not args.no_dependency)
    mm = ModuleManager(args.path, verbose=True)
    try:
        if args.all_files:
            for file in os.listdir(args.path):
                _, ext = os.path.splitext(file)
                if ext == ".py":
                    mm.addEntry(file=file)
        if args.files:
            for file in args.files:
                mm.addEntry(file=file)
        if args.modules:
            for module in args.modules:
                mm.addEntry(module=module)
    # except ModuleNotFoundException as e:
    #    print(f"Error: {e}")
    #    exit()
    except ValueError as e:
        print(f"Error: {e}")
        exit()

    print("IR generation is done, start Point-to Analysis...                ")
    if args.context_sensitive:
        analysis = CSAnalysis(verbose=True)
    else:
        analysis = Analysis(verbose=True)
    # analysis = Analysis(verbose=True)

    entrys = mm.getEntrys()
    analysis.analyze(entrys)
    print("Point-to Analysis is done, start writing to file                ")

    print(analysis.pointToSet.to_json())

    # fp = open(args.output, "w")
    # callgraph = analysis.callgraph.export()  # In some version of Python3, no export() method?
    # if args.include:
    #    callgraph = {k: v for k, v in callgraph.items() if k.startswith(args.include)}
    # json.dump(callgraph, fp, indent=4)
    # fp.close()

    print("All done.")
