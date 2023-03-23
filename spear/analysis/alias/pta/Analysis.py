from collections import defaultdict
from typing import Dict, List, Set, Tuple, Union

from spear.analysis.alias.pta.ObjectPool import OBJ_BUILTIN, OBJ_CLASS, OBJ_CLASS_METHOD, OBJ_FAKE, OBJ_FUNCTION, \
    OBJ_MODULE, OBJ_STATIC_METHOD, OBJ_SUPER, ObjectPool
from spear.analysis.alias.pta.AttrGraph import AttrGraph
from spear.analysis.alias.pta.BindingStmts import BindingStmts
from spear.analysis.alias.pta.class_hiearchy import MRO, ClassHiearchy
from spear.analysis.alias.pta.Objects import ClassMethodObject, ClassObject, FakeObject, FunctionObject, Object, \
    StaticMethodObject, SuperObject
from spear.analysis.alias.pta.PointToSet import PointToSet
from spear.analysis.alias.pta.PointerFlow import PointerFlow
from spear.analysis.alias.pta.Pointers import AttrPtr, Pointer, VarPtr

from spear.analysis.alias.ir.class_code_block import ClassCodeBlock
from spear.analysis.alias.ir.code_block import CodeBlock
from spear.analysis.alias.ir.ir_stmts import Assign, Call, DelAttr, GetAttr, IRStmt, NewBuiltin, NewClass, \
    NewFunction, NewModule, NewStaticMethod, NewSuper, SetAttr, Variable
from spear.analysis.alias.ir.ModuleCodeBlock import ModuleCodeBlock

FAKE_PREFIX = "$r_"


# builtin_functions = ["abs", "aiter", "all", "any", "anext", "ascii", "bin", "bool", "breakpoint",
# "bytearray", "bytes", "callable", "chr", "classmethod", "compile", "complex", "delattr",
# "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter", "float", "format", "frozenset",
# "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
# "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min", "next",
# "object", "oct", "open", "ord", "pow", "print", "property", "range", "repr", "reversed", "round",
# "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple", "type",
# "vars", "zip", "__import__"]

def isFakeAttr(attr: str):
    return attr.startswith(FAKE_PREFIX)


Resolver = Union[ClassObject, SuperObject]
ResolveInfo = Tuple[Resolver, MRO, int]

ADD_POINTS_TO = 1
BIND_STMT = 2


class Analysis:
    pointToSet: PointToSet
    callgraph: Dict[str, Set[str]]
    pointerFlow: PointerFlow
    attrGraph: AttrGraph

    # defined: Set[CodeBlock]
    classHiearchy: ClassHiearchy
    persist_attr: Dict[ClassObject, Dict[str, Set[ResolveInfo]]]
    resolved_attr: Dict[Resolver, Set[str]]
    workList: List[Tuple[Pointer, Set[Object]]]

    def __init__(self, verbose=False):
        self.pointToSet = PointToSet()
        self.callgraph = defaultdict(set)
        self.pointerFlow = PointerFlow()
        self.attrGraph = AttrGraph()
        self.bindingStmts = BindingStmts()
        self.objectPool = ObjectPool()
        self.reachable = set()
        self.classHiearchy = ClassHiearchy(self.pointToSet)
        self.persist_attr = defaultdict(dict)
        self.resolved_attr = defaultdict(set)
        self.workList = []
        self.verbose = verbose

        self.processStmts = {
            # "GetAttr": self.processGetAttr,
            # "SetAttr": self.processSetAttr,
            "NewClass": self.processNewClass,
            "Call": self.processCall,
            "DelAttr": self.processDelAttr,
            "NewStaticMethod": self.processNewStaticMethod,
            # "NewClassMethod": self.processNewClassMethod,
            "NewSuper": self.processNewSuper,

        }

    # addAll mean treat all codeblocks in this codeBlock as reachable.
    def addReachable(self, code_block: CodeBlock):
        if not code_block or code_block in self.reachable:
            return
        self.reachable.add(code_block)

        # Add codes into the pool
        for stmt in code_block.stmts:
            self.workList.append((BIND_STMT, stmt))

        for stmt in code_block.stmts:
            if isinstance(stmt, Assign):
                source_ptr = VarPtr.create(stmt.source)
                target_ptr = VarPtr.create(stmt.target)
                self.addFlow(source_ptr, target_ptr)

            elif isinstance(stmt, GetAttr):
                source_ptr = VarPtr.create(stmt.source)
                target_ptr = VarPtr.create(stmt.target)
                self.attrGraph.putGet(target_ptr, source_ptr, stmt.attr)
                self.addGetEdge(target_ptr, source_ptr, stmt.attr, self.pointToSet.get(source_ptr))

            elif isinstance(stmt, SetAttr):
                source_ptr = VarPtr.create(stmt.source)
                target_ptr = VarPtr.create(stmt.target)
                self.attrGraph.putSet(target_ptr, source_ptr, stmt.attr)
                self.addSetEdge(target_ptr, source_ptr, stmt.attr, self.pointToSet.get(target_ptr))

            elif isinstance(stmt, NewModule):
                if isinstance(stmt.module, ModuleCodeBlock):
                    obj = self.objectPool.create(OBJ_MODULE, stmt.module)
                    target_ptr = VarPtr.create(stmt.target)
                    global_ptr = VarPtr.create(stmt.module.globalVariable)
                    self.workList.append((ADD_POINTS_TO, target_ptr, {obj}))
                    self.workList.append((ADD_POINTS_TO, global_ptr, {obj}))
                    # self.addDefined(stmt.module)
                    self.addReachable(stmt.module)
                    # self.callgraph.put(stmt, stmt.module)
                else:
                    obj = self.objectPool.create(OBJ_FAKE, stmt.module)
                    target_ptr = VarPtr.create(stmt.target)
                    self.workList.append((ADD_POINTS_TO, target_ptr, {obj}))

            elif isinstance(stmt, NewFunction):
                obj = self.objectPool.create(OBJ_FUNCTION, stmt)
                target_ptr = VarPtr.create(stmt.target)
                self.workList.append((ADD_POINTS_TO, target_ptr, {obj}))

            elif isinstance(stmt, NewClass):
                obj = self.objectPool.create(OBJ_CLASS, stmt)
                target_ptr = VarPtr.create(stmt.target)
                this_ptr = VarPtr.create(stmt.codeBlock.thisClassVariable)
                self.workList.append((ADD_POINTS_TO, target_ptr, {obj}))
                self.workList.append((ADD_POINTS_TO, this_ptr, {obj}))

                self.classHiearchy.addClass(obj)

                for attr in obj.attributes:
                    self.persist_attr[obj][attr] = set()

                self.addReachable(stmt.codeBlock)
                # self.callgraph.put(stmt, stmt.codeBlock)
                self.addCallEdge(stmt, obj.readable_name)

            elif isinstance(stmt, NewBuiltin):
                target_ptr = VarPtr.create(stmt.target)
                # if(stmt.value is not None or stmt.type == "NoneType"):
                #     obj = ConstObject(stmt.value)
                # else:
                obj = self.objectPool.create(OBJ_BUILTIN, stmt)
                self.workList.append((ADD_POINTS_TO, target_ptr, {obj}))

    def analyze(self, entrys: CodeBlock):
        for entry in entrys:
            if isinstance(entry, ModuleCodeBlock):
                obj = self.objectPool.create(OBJ_MODULE, entry)
                self.workList.append((ADD_POINTS_TO, VarPtr.create(entry.globalVariable), {obj}))
            self.addReachable(entry)

        while len(self.workList) > 0:

            if self.verbose:
                print(f"PTA worklist remains {len(self.workList):<10} to process.                \r", end="")

            type, *args = self.workList[0]
            del self.workList[0]

            if type == ADD_POINTS_TO:
                ptr, objs = args
                if len(objs) == 0:
                    continue

                objs = self.pointToSet.putAll(ptr, objs)
                if objs:
                    for succ in self.pointerFlow.successors(ptr):
                        self.flow(ptr, succ, objs)

                if not isinstance(ptr, VarPtr):
                    continue
                for target, attr in self.attrGraph.getTargets(ptr):
                    self.addGetEdge(target, ptr, attr, objs)

                for source, attr in self.attrGraph.setSources(ptr):
                    self.addSetEdge(ptr, source, attr, objs)

                for opname, process in self.processStmts.items():
                    for stmt_info in self.bindingStmts.get(opname, ptr):
                        process(stmt_info, objs)

            if type == BIND_STMT:
                stmt, = args

                # if(isinstance(stmt, SetAttr)):
                #     # print(f"Bind SetAttr: {stmt.target} - {stmt}")
                #     varPtr = VarPtr.create(stmt.target)
                #     stmt_info = (stmt, )
                #     self.bindingStmts.bind("SetAttr", varPtr, stmt_info)
                #     self.processSetAttr(stmt_info, self.pointToSet.get(varPtr))

                # elif(isinstance(stmt, GetAttr)):
                #     # print(f"Bind GetAttr: {stmt.source} - {stmt}")
                #     varPtr = VarPtr.create(stmt.source)
                #     stmt_info = (stmt, )
                #     self.bindingStmts.bind("GetAttr", varPtr, stmt_info)
                #     self.processGetAttr(stmt_info, self.pointToSet.get(varPtr))

                if isinstance(stmt, NewClass):
                    for i in range(len(stmt.bases)):
                        # print(f"Bind Base: {stmt.bases[i]} - {stmt} - {i}")
                        var_ptr = VarPtr.create(stmt.bases[i])
                        stmt_info = (stmt, i)
                        self.bindingStmts.bind("NewClass", var_ptr, stmt_info)
                        self.processNewClass(stmt_info, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, Call):
                    # print(f"Bind Call: {stmt.callee} - {stmt}")
                    var_ptr = VarPtr.create(stmt.callee)
                    stmt_info = (stmt,)
                    self.bindingStmts.bind("Call", var_ptr, stmt_info)
                    self.processCall(stmt_info, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, DelAttr):
                    # print(f"Bind DelAttr: {stmt.var} - {stmt}")
                    var_ptr = VarPtr.create(stmt.var)
                    stmt_info = (stmt,)
                    self.bindingStmts.bind("DelAttr", var_ptr, stmt_info)
                    self.processDelAttr(stmt_info, self.pointToSet.get(var_ptr))

                # elif(isinstance(stmt, NewClassMethod)):
                #     varPtr = VarPtr.create(stmt.func)
                #     stmt_info = (stmt, )
                #     self.bindingStmts.bind("NewClassMethod", varPtr, stmt_info)
                #     self.processNewClassMethod(stmt_info, self.pointToSet.get(varPtr))

                elif isinstance(stmt, NewStaticMethod):
                    var_ptr = VarPtr.create(stmt.func)
                    stmt_info = (stmt,)
                    self.bindingStmts.bind("NewStaticMethod", var_ptr, stmt_info)
                    self.processNewStaticMethod(stmt_info, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, NewSuper):

                    var_ptr = VarPtr.create(stmt.type)
                    stmt_info = (stmt, "type")
                    self.bindingStmts.bind("NewSuper", var_ptr, stmt_info)
                    self.processNewSuper(stmt_info, self.pointToSet.get(var_ptr))

                    var_ptr = VarPtr.create(stmt.bound)
                    stmt_info = (stmt, "bound")
                    self.bindingStmts.bind("NewSuper", var_ptr, stmt_info)
                    self.processNewSuper(stmt_info, self.pointToSet.get(var_ptr))

    def addFlow(self, source: Pointer, target: Pointer):
        if self.pointerFlow.put(source, target):
            # print(f"Add Flow:{source} -> {target}")
            objs = self.pointToSet.get(source)
            self.flow(source, target, objs)

    # Some objects flow from source to target
    # this function is needed because some transforming need to be done
    def flow(self, source: Pointer, target: Pointer, objs: Set[Object]):
        # do some transform
        new_objs = objs
        if isinstance(target, AttrPtr) and isFakeAttr(target.attr):

            if isinstance(target.obj, ClassObject):
                new_objs = self.transformObj_Class(target.obj, objs)
            elif isinstance(target.obj, SuperObject):

                new_objs = self.transformObj_Class(target.obj.bound, objs)

        self.workList.append((ADD_POINTS_TO, target, new_objs))

    # def transformObj_Instance(self, insObj: InstanceObject, objs) -> Set[Object]:
    #     newObjs = set()
    #     for obj in objs:
    #         if(isinstance(obj, FunctionObject)):
    #             newObjs.add(InstanceMethodObject(insObj, obj))
    #         elif(isinstance(obj, ClassMethodObject)):
    #             func = obj.func
    #             newObjs.add(ClassMethodObject(insObj.type, func))
    #         else:
    #             newObjs.add(obj)
    #     return newObjs

    def transformObj_Class(self, class_obj: ClassObject, objs) -> Set[Object]:
        new_objs = set()
        for obj in objs:
            # if(isinstance(obj, ClassMethodObject)):
            #     func = obj.func
            #     new_objs.add(ClassMethodObject(classObj, func))
            # else:
            #     new_objs.add(obj)
            if isinstance(obj, FunctionObject):
                new_obj = self.objectPool.create(OBJ_CLASS_METHOD, class_obj, obj)
                new_objs.add(new_obj)
            else:
                new_objs.add(obj)
        return new_objs

    # classObj.$r_attr <- parent.attr
    # where parent is the first class that has this attr as its persistent attributes along MRO
    def resolveAttribute(self, obj: Resolver, attr: str, resolve_info: Tuple[MRO, int]):

        mro, start = resolve_info

        child_attr = AttrPtr(obj, FAKE_PREFIX + attr)
        for i in range(start, len(mro)):
            parent = mro[i]
            parent_attr = AttrPtr(parent, attr)
            self.addFlow(parent_attr, child_attr)
            try:
                self.persist_attr[parent][attr].add((obj, mro, i))
                break
            except KeyError:
                pass

    def resolveAttrIfNot(self, obj: Resolver, attr: str):

        if attr in self.resolved_attr[obj]:
            return

        self.resolved_attr[obj].add(attr)
        if isinstance(obj, ClassObject):
            class_obj = obj
        elif isinstance(obj, SuperObject):
            # if(isinstance(obj.bound, InstanceObject)):
            #     class_obj = obj.bound.type
            # else:
            class_obj = obj.bound

        for mro in self.classHiearchy.getMROs(class_obj):
            if isinstance(obj, ClassObject):
                start = 0
            elif isinstance(obj, SuperObject):
                for start in range(len(mro)):
                    if mro[start] == obj.type:
                        # start from the one right after type
                        start += 1
                        break
            self.resolveAttribute(obj, attr, (mro, start))

    def addSetEdge(self, target: VarPtr, source: VarPtr, attr: str, objs: Set[Object]):
        # stmt,  = *stmtInfo,
        # assert(isinstance(stmt, SetAttr))
        for obj in objs:
            attr_ptr = AttrPtr(obj, attr)
            self.addFlow(source, attr_ptr)

    def addGetEdge(self, target: VarPtr, source: VarPtr, attr: str, objs: Set[Object]):
        # stmt, = *stmtInfo, 
        # assert(isinstance(stmt, GetAttr))
        for obj in objs:

            if isinstance(obj, FakeObject):
                fake_obj = self.objectPool.create(OBJ_FAKE, obj, (source, target, attr))
                self.workList.append((ADD_POINTS_TO, target, {fake_obj}))

            # elif(isinstance(obj, InstanceObject)):
            #     # target <- instance.attr
            #     insAttr = AttrPtr(obj, stmt.attr)
            #     insResAttr = AttrPtr(obj, FAKE_PREFIX + stmt.attr)
            #     self.addFlow(insAttr, varPtr)
            #     self.addFlow(insResAttr, varPtr)
            #     classObj = obj.type
            #     self.resolveAttrIfNot(classObj, stmt.attr)
            #     # instance.attr <- class.$r_attr
            #     class_attr = AttrPtr(classObj, FAKE_PREFIX + stmt.attr)
            #     self.addFlow(class_attr, insResAttr)

            if isinstance(obj, ClassObject):
                self.resolveAttrIfNot(obj, attr)
                # instance.attr <- class.$r_attr
                class_attr = AttrPtr(obj, FAKE_PREFIX + attr)
                self.addFlow(class_attr, target)

            elif isinstance(obj, SuperObject):
                self.resolveAttrIfNot(obj, attr)
                # instance.attr <- class.$r_attr
                super_attr = AttrPtr(obj, FAKE_PREFIX + attr)
                self.addFlow(super_attr, target)

            else:
                attr_ptr = AttrPtr(obj, attr)
                self.addFlow(attr_ptr, target)

    def processNewClass(self, stmt_info: Tuple[NewClass, int], objs: Set[Object]):
        stmt, index = *stmt_info,
        assert (isinstance(stmt, NewClass))
        mro_change = set()
        for obj in objs:
            if isinstance(obj, ClassObject):
                cls = self.objectPool.create(OBJ_CLASS, stmt)
                mro_change |= self.classHiearchy.addClassBase(cls, index, obj)
        for mro in mro_change:
            class_obj = mro[0]

            for attr in self.resolved_attr[class_obj]:
                self.resolveAttribute(class_obj, attr, (mro, 0))

    def processCall(self, stmt_info: Tuple[Call], objs: Set[Object]):
        stmt, = *stmt_info,
        assert (isinstance(stmt, Call))
        var_ptr = VarPtr.create(stmt.target)
        new_objs = set()
        for obj in objs:
            # if(isinstance(obj, FakeObject)):
            #     func = obj.getCodeBlock()
            #     self.callgraph.put(stmt, func)
            if isinstance(obj, FunctionObject):

                self.matchArgParam(pos_args=[VarPtr.create(posArg) for posArg in stmt.posargs],
                                   kw_args={kw: VarPtr.create(kwarg) for kw, kwarg in stmt.kwargs.items()},
                                   pos_params=obj.posParams,
                                   kw_params=obj.kwParams,
                                   var_param=obj.varParam,
                                   kw_param=obj.kwParam)
                ret_var = obj.retVar
                res_var = VarPtr.create(stmt.target)
                self.addFlow(ret_var, res_var)
                self.addReachable(obj.codeBlock)
                self.addCallEdge(stmt, obj.readable_name)

            # elif(isinstance(obj, InstanceMethodObject)):
            #     func = obj.func.getCodeBlock()
            #     pos_params = [VarPtr.create(param) for param in func.posargs]
            #     if(len(pos_params) == 0):
            #         # not a method, just skip
            #         continue
            #     self.workList.append((ADD_POINT_TO, pos_params[0], {obj.selfObj}))
            #     del pos_params[0]
            #     self.matchArgParam(posArgs=         [VarPtr.create(posArg) for posArg in stmt.posargs],
            #                         kwArgs=         {kw:VarPtr.create(kwarg) for kw, kwarg in stmt.kwargs.items()},
            #                         pos_params=      pos_params,
            #                         kwParams=       {kw:VarPtr.create(kwOnlyParam) for kw, kwOnlyParam in func.kwargs.items()},
            #                         varParam=       VarPtr.create(func.vararg) if func.vararg else None,
            #                         kwParam=        VarPtr.create(func.kwarg) if func.kwarg else None)
            #     ret_var = VarPtr.create(func.returnVariable)
            #     res_var = VarPtr.create(stmt.target)
            #     self.addFlow(ret_var, res_var)
            #     self.callgraph.put(stmt, func)
            #     self.addReachable(func)

            elif isinstance(obj, ClassMethodObject):
                func_obj = obj.func
                pos_params = func_obj.posParams[:]
                if len(pos_params) == 0:
                    # not a method, just skip
                    continue
                self.workList.append((ADD_POINTS_TO, pos_params[0], {obj.classObj}))
                del pos_params[0]
                self.matchArgParam(pos_args=[VarPtr.create(posArg) for posArg in stmt.posargs],
                                   kw_args={kw: VarPtr.create(kwarg) for kw, kwarg in stmt.kwargs.items()},
                                   pos_params=pos_params,
                                   kw_params=func_obj.kwParams,
                                   var_param=func_obj.varParam,
                                   kw_param=func_obj.kwParam)
                ret_var = func_obj.retVar
                res_var = VarPtr.create(stmt.target)
                self.addFlow(ret_var, res_var)
                self.addCallEdge(stmt, func_obj.readable_name)
                self.addReachable(func_obj.codeBlock)

            elif isinstance(obj, StaticMethodObject):
                func_obj = obj.func
                self.matchArgParam(pos_args=[VarPtr.create(posArg) for posArg in stmt.posargs],
                                   kw_args={kw: VarPtr.create(kwarg) for kw, kwarg in stmt.kwargs.items()},
                                   pos_params=func_obj.posParams,
                                   kw_params=func_obj.kwParams,
                                   var_param=func_obj.varParam,
                                   kw_param=func_obj.kwParam)
                ret_var = func_obj.retVar
                res_var = VarPtr.create(stmt.target)
                self.addFlow(ret_var, res_var)
                self.addReachable(func_obj.codeBlock)
                self.addCallEdge(stmt, func_obj.readable_name)

            elif isinstance(obj, ClassObject):
                # insObj = CIInstanceObject(stmt, obj)

                # target <- instance.attr
                # insAttr = AttrPtr(insObj, FAKE_PREFIX + "__init__")
                class_attr = AttrPtr(obj, FAKE_PREFIX + "__init__")
                # self.addFlow(class_attr, insAttr)
                self.resolveAttrIfNot(obj, "__init__")

                init = Variable(f"$init_method_of_{obj.id}", stmt.belongsTo)
                init_ptr = VarPtr.create(init)
                self.addFlow(class_attr, init_ptr)
                new_stmt = Call(Variable("", stmt.belongsTo), init, stmt.posargs, stmt.kwargs, stmt.belongsTo,
                                stmt.belongsTo.getNewID())
                self.workList.append((BIND_STMT, new_stmt))
                new_objs.add(obj)
        if new_objs:
            self.workList.append((ADD_POINTS_TO, var_ptr, new_objs))

    def matchArgParam(self, /, pos_args: List[VarPtr],
                      kw_args: Dict[str, VarPtr],
                      pos_params: List[VarPtr],
                      kw_params: Dict[str, VarPtr],
                      var_param: VarPtr, kw_param: VarPtr):

        pos_count = len(pos_params)
        for i in range(len(pos_args)):
            if i < pos_count:
                self.addFlow(pos_args[i], pos_params[i])
            elif var_param:
                self.addFlow(pos_args[i], var_param)

        for kw, varPtr in kw_args.items():
            if kw in kw_params:
                self.addFlow(varPtr, kw_params[kw])
            elif kw_param:
                self.addFlow(kw_args[kw], kw_param)

    def processDelAttr(self, stmt_info: Tuple[DelAttr], objs: Set[Object]):
        stmt, = *stmt_info,
        assert (isinstance(stmt, DelAttr))
        attr = stmt.attr
        for obj in objs:
            if attr in self.persist_attr[obj]:
                for resolver, mro, index in self.persist_attr[obj][attr]:
                    self.resolveAttribute(resolver, attr, (mro, index + 1))
                del self.persist_attr[obj][attr]

    # def processNewClassMethod(self, stmtInfo: Tuple[NewClassMethod], objs: Set[Object]):
    #     stmt, = *stmtInfo, 
    #     assert(isinstance(stmt, NewClassMethod))
    #     target = VarPtr.create(stmt.target)
    #     newObjs = set()
    #     for obj in objs:
    #         if(isinstance(obj, FunctionObject) and isinstance(stmt.belongsTo, ClassCodeBlock)):

    #             for classObj in self.pointToSet.get(VarPtr.create(stmt.belongsTo.thisClassVariable)):
    #                 if(isinstance(classObj, ClassObject)):
    #                     classMethod = ClassMethodObject(classObj, obj)
    #                     newObjs.add(classMethod)
    #     if(newObjs):
    #         self.workList.append((ADD_POINT_TO, target, newObjs))

    def processNewStaticMethod(self, stmt_info: Tuple[NewStaticMethod], objs: Set[Object]):
        stmt, = *stmt_info,
        assert (isinstance(stmt, NewStaticMethod))
        target = VarPtr.create(stmt.target)
        new_objs = set()
        for obj in objs:
            if isinstance(obj, FunctionObject) and isinstance(stmt.belongsTo, ClassCodeBlock):
                static_method = self.objectPool.create(OBJ_STATIC_METHOD, obj)
                new_objs.add(static_method)
        if new_objs:
            self.workList.append((ADD_POINTS_TO, target, new_objs))

    def processNewSuper(self, stmt_info: NewSuper, objs: Set[Object]):
        stmt, operand = *stmt_info,
        assert (isinstance(stmt, NewSuper))
        if operand == "type":
            new_objs = set()
            target = VarPtr.create(stmt.target)
            for obj in objs:
                if isinstance(obj, ClassObject):
                    for boundObj in self.pointToSet.get(VarPtr.create(stmt.bound)):
                        new_obj = self.objectPool.create(OBJ_SUPER, obj, boundObj)
                        new_objs.add(new_obj)
            if new_objs:
                self.workList.append((ADD_POINTS_TO, target, new_objs))
        else:
            new_objs = set()
            target = VarPtr.create(stmt.target)
            for obj in objs:
                if isinstance(obj, ClassObject):
                    for typeObj in self.pointToSet.get(VarPtr.create(stmt.type)):
                        new_obj = self.objectPool.create(OBJ_SUPER, typeObj, obj)
                        new_objs.add(new_obj)
            if new_objs:
                self.workList.append((ADD_POINTS_TO, target, new_objs))

    def addCallEdge(self, callsite: IRStmt, callee: str):
        self.callgraph[callsite.belongsTo.readable_name].add(callee)
