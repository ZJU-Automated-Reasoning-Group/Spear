from typing import Dict, List, Set, Tuple, Union
import typing
from Spear.Analysis.Alias.IR.ClassCodeBlock import ClassCodeBlock
from Spear.Analysis.Alias.IR.ModuleCodeBlock import ModuleCodeBlock

if typing.TYPE_CHECKING:
    from Spear.Analysis.Alias.CSPTA import CS_Call, CS_DelAttr, CS_GetAttr, CS_NewClass, CS_SetAttr, \
        CSCodeBlock, CS_NewClassMethod, CS_NewStaticMethod, CS_NewSuper

from Spear.Analysis.Alias.CSPTA.CSPointers import CSVarPtr
from Spear.Analysis.Alias.CSPTA.CSObjects import CSBuiltinObject, CSClassObject, \
    CSFunctionObject, CSInstanceObject, CSObject
from Spear.Analysis.Alias.CSPTA.Context import emptyContextChain, selectContext

from Spear.Analysis.Alias.PTA.Objects import ClassMethodObject, ClassObject, FakeObject, \
    FunctionObject, ModuleObject, Object, StaticMethodObject, SuperObject
from Spear.Analysis.Alias.PTA.Pointers import AttrPtr, Pointer
from Spear.Analysis.Alias.PTA.BindingStmts import BindingStmts
from Spear.Analysis.Alias.PTA.PointerFlow import PointerFlow
from Spear.Analysis.Alias.PTA.CallGraph import CallGraph
from Spear.Analysis.Alias.PTA.PointToSet import PointToSet
from Spear.Analysis.Alias.PTA.ClassHiearchy import MRO, ClassHiearchy
from Spear.Analysis.Alias.PTA.Objects import InstanceObject, InstanceMethodObject

from Spear.Analysis.Alias.IR.IRStmts import Assign, Call, DelAttr, GetAttr, NewBuiltin, NewClass, \
    NewClassMethod, NewFunction, NewModule, NewStaticMethod, NewSuper, SetAttr, Variable


FAKE_PREFIX = "$r_"


def isFakeAttr(attr: str):
    return attr.startswith(FAKE_PREFIX)


Resolver = Union[ClassObject, SuperObject]
ResolveInfo = Tuple[Resolver, MRO, int]

ADD_POINT_TO = 1
BIND_STMT = 2


class CSAnalysis:
    pointToSet: PointToSet
    callgraph: CallGraph
    pointerFlow: PointerFlow
    bindingStmts: BindingStmts
    reachable: Set['CSCodeBlock']
    resolved_attr: Dict[Resolver, Set[str]]
    classHiearchy: ClassHiearchy
    persist_attr: Dict[CSClassObject, Dict[str, Set[ResolveInfo]]]
    workList: List[Tuple[Pointer, Set[Object]]]

    def __init__(self, verbose=False):
        self.pointToSet = PointToSet()
        self.callgraph = CallGraph()
        self.pointerFlow = PointerFlow()
        self.bindingStmts = BindingStmts()
        self.defined = set()
        self.reachable = set()
        self.classHiearchy = ClassHiearchy(self.pointToSet)
        self.resolved_attr = {}
        self.persist_attr = {}
        self.workList = []
        self.verbose = verbose

    def addReachable(self, cs_code_block: 'CSCodeBlock'):
        if cs_code_block in self.reachable:
            return
        self.reachable.add(cs_code_block)

        ctx, code_block = cs_code_block
        # Add codes into the pool
        for stmt in code_block.stmts:
            cs_stmt = (ctx, stmt)
            self.workList.append((BIND_STMT, cs_stmt))

        for stmt in code_block.stmts:
            cs_stmt = (ctx, stmt)
            if isinstance(stmt, Assign):
                source_ptr = CSVarPtr(ctx, stmt.source)
                target_ptr = CSVarPtr(ctx, stmt.target)
                self.addFlow(source_ptr, target_ptr)

            elif isinstance(stmt, NewModule):
                if isinstance(stmt.module, ModuleCodeBlock):
                    obj = ModuleObject(stmt.module)

                    target_ptr = CSVarPtr(ctx, stmt.target)
                    global_ptr = CSVarPtr(ctx, stmt.module.globalVariable)

                    self.workList.append((ADD_POINT_TO, target_ptr, {obj}))
                    self.workList.append((ADD_POINT_TO, global_ptr, {obj}))

                    cs_code_block = (emptyContextChain(), stmt.module)
                    self.addReachable(cs_code_block)
                    # self.callgraph.put(cs_stmt, csCodeBlock)
                else:
                    obj = FakeObject(stmt.module, None)
                    target_ptr = CSVarPtr(ctx, stmt.target)
                    self.workList.append((ADD_POINT_TO, target_ptr, {obj}))

            elif isinstance(stmt, NewFunction):
                obj = CSFunctionObject(cs_stmt)
                target_ptr = CSVarPtr(ctx, stmt.target)
                self.workList.append((ADD_POINT_TO, target_ptr, {obj}))

            elif isinstance(stmt, NewClass):
                obj = CSClassObject(cs_stmt)
                target_ptr = CSVarPtr(ctx, stmt.target)

                this_ptr = CSVarPtr(ctx, stmt.codeBlock.thisClassVariable)
                self.workList.append((ADD_POINT_TO, target_ptr, {obj}))
                self.workList.append((ADD_POINT_TO, this_ptr, {obj}))

                cs_code_block = (ctx, stmt.codeBlock)
                self.addReachable(cs_code_block)
                self.callgraph.put(stmt, stmt.codeBlock)

                self.classHiearchy.addClass(obj)
                self.persist_attr[obj] = {}
                for attr in obj.getAttributes():
                    self.persist_attr[obj][attr] = set()

            elif isinstance(stmt, NewBuiltin):
                target_ptr = CSVarPtr(ctx, stmt.target)
                # if(stmt.value is not None or stmt.type == "NoneType"):
                #     obj = ConstObject(stmt.value)
                # else:
                obj = CSBuiltinObject(cs_stmt)
                self.workList.append((ADD_POINT_TO, target_ptr, {obj}))

    def analyze(self, entrys: ModuleCodeBlock):
        for entry in entrys:
            obj = ModuleObject(entry)
            self.workList.append((ADD_POINT_TO, CSVarPtr(emptyContextChain(), entry.globalVariable), {obj}))
            self.addReachable((emptyContextChain(), entry))

        while len(self.workList) > 0:
            if self.verbose:
                print(f"PTA worklist remains {len(self.workList)} to process.                \r", end="")
            type, *args = self.workList[0]
            del self.workList[0]

            if type == ADD_POINT_TO:
                ptr, objs = args

                if len(objs) == 0:
                    continue

                objs = self.pointToSet.putAll(ptr, objs)
                for succ in self.pointerFlow.successors(ptr):
                    self.flow(ptr, succ, objs)

                if not isinstance(ptr, CSVarPtr):
                    continue

                for cs_stmt in self.bindingStmts.getSetAttr(ptr):
                    self.processSetAttr(cs_stmt, objs)

                for cs_stmt in self.bindingStmts.getGetAttr(ptr):
                    self.processGetAttr(cs_stmt, objs)

                for cs_stmt, index in self.bindingStmts.getNewClass(ptr):
                    self.processNewClass(cs_stmt, index, objs)

                for cs_stmt in self.bindingStmts.getCall(ptr):
                    self.processCall(cs_stmt, objs)

                for cs_stmt in self.bindingStmts.getDelAttr(ptr):
                    self.processDelAttr(cs_stmt, objs)

                for cs_stmt in self.bindingStmts.getNewClassMethod(ptr):
                    self.processNewClassMethod(cs_stmt, objs)

                for cs_stmt in self.bindingStmts.getNewStaticMethod(ptr):
                    self.processNewStaticMethod(cs_stmt, objs)

                for cs_stmt in self.bindingStmts.getNewSuper_type(ptr):
                    self.processNewSuper_type(cs_stmt, objs)

                for cs_stmt in self.bindingStmts.getNewSuper_bound(ptr):
                    self.processNewSuper_bound(cs_stmt, objs)

            if type == BIND_STMT:
                cs_stmt, = args
                ctx, stmt = cs_stmt

                if isinstance(stmt, SetAttr):
                    # print(f"Bind SetAttr: {stmt.target} - {csStmt}")
                    var_ptr = CSVarPtr(ctx, stmt.target)
                    self.bindingStmts.bindSetAttr(var_ptr, cs_stmt)
                    self.processSetAttr(cs_stmt, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, GetAttr):
                    # print(f"Bind GetAttr: {stmt.source} - {csStmt}")
                    var_ptr = CSVarPtr(ctx, stmt.source)
                    self.bindingStmts.bindGetAttr(var_ptr, cs_stmt)
                    self.processGetAttr(cs_stmt, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, NewClass):
                    for i in range(len(stmt.bases)):
                        # print(f"Bind Base: {stmt.bases[i]} - {csStmt} - {i}")
                        var_ptr = CSVarPtr(ctx, stmt.bases[i])
                        self.bindingStmts.bindNewClass(var_ptr, cs_stmt, i)
                        self.processNewClass(cs_stmt, i, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, Call):
                    # print(f"Bind Call: {stmt.callee} - {csStmt}")
                    var_ptr = CSVarPtr(ctx, stmt.callee)
                    self.bindingStmts.bindCall(var_ptr, cs_stmt)
                    self.processCall(cs_stmt, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, DelAttr):
                    # print(f"Bind DelAttr: {stmt.var} - {csStmt}")
                    var_ptr = CSVarPtr(ctx, stmt.var)
                    self.bindingStmts.bindDelAttr(var_ptr, cs_stmt)
                    self.processDelAttr(cs_stmt, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, NewClassMethod):
                    var_ptr = CSVarPtr(ctx, stmt.func)
                    self.bindingStmts.bindNewClassMethod(var_ptr, cs_stmt)
                    self.processNewClassMethod(cs_stmt, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, NewStaticMethod):
                    var_ptr = CSVarPtr(ctx, stmt.func)
                    self.bindingStmts.bindNewStaticMethod(var_ptr, cs_stmt)
                    self.processNewStaticMethod(cs_stmt, self.pointToSet.get(var_ptr))

                elif isinstance(stmt, NewSuper):
                    var_ptr = CSVarPtr(ctx, stmt.type)
                    self.bindingStmts.bindNewSuper_type(var_ptr, cs_stmt)
                    self.processNewSuper_type(cs_stmt, self.pointToSet.get(var_ptr))

                    var_ptr = CSVarPtr(ctx, stmt.bound)
                    self.bindingStmts.bindNewSuper_bound(var_ptr, cs_stmt)
                    self.processNewSuper_bound(cs_stmt, self.pointToSet.get(var_ptr))

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

            if isinstance(target.obj, InstanceObject):
                new_objs = self.transformObj_Instance(target.obj, objs)

            elif isinstance(target.obj, ClassObject):
                new_objs = self.transformObj_Class(target.obj, objs)
            elif isinstance(target.obj, SuperObject):
                if isinstance(target.obj.bound, InstanceObject):
                    new_objs = self.transformObj_Instance(target.obj.bound, objs)
                else:
                    new_objs = self.transformObj_Class(target.obj.bound, objs)

        self.workList.append((ADD_POINT_TO, target, new_objs))

    def transformObj_Instance(self, ins_obj: InstanceObject, objs) -> Set[Object]:
        new_objs = set()
        for obj in objs:
            if isinstance(obj, FunctionObject):
                new_objs.add(InstanceMethodObject(ins_obj, obj))
            elif isinstance(obj, ClassMethodObject):
                func = obj.func
                new_objs.add(ClassMethodObject(ins_obj.type, func))
            else:
                new_objs.add(obj)
        return new_objs

    def transformObj_Class(self, class_obj: ClassObject, objs) -> Set[Object]:
        new_objs = set()
        for obj in objs:
            if isinstance(obj, ClassMethodObject):
                func = obj.func
                new_objs.add(ClassMethodObject(class_obj, func))
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
                self.persist_attr[parent][attr].add((mro, i))
                break
            except KeyError:
                pass

    def resolveAttrIfNot(self, obj: Resolver, attr: str):
        if obj in self.resolved_attr:
            if attr in self.resolved_attr[obj]:
                return
        else:
            self.resolved_attr[obj] = set()

        self.resolved_attr[obj].add(attr)

        if isinstance(obj, ClassObject):
            class_obj = obj
        elif isinstance(obj, SuperObject):
            if isinstance(obj.bound, InstanceObject):
                class_obj = obj.bound.type
            else:
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

    def processSetAttr(self, cs_stmt: 'CS_SetAttr', objs: Set[CSObject]):
        # print(f"Process SetAttr: {csStmt}")
        assert (isinstance(cs_stmt[1], SetAttr))
        ctx, stmt = cs_stmt
        for obj in objs:
            attr_ptr = AttrPtr(obj, stmt.attr)
            self.addFlow(CSVarPtr(ctx, stmt.source), attr_ptr)

    def processGetAttr(self, cs_stmt: 'CS_GetAttr', objs: Set[Object]):
        # print(f"Process GetAttr: {csStmt}")
        assert (isinstance(cs_stmt[1], GetAttr))
        ctx, stmt = cs_stmt
        for obj in objs:
            var_ptr = CSVarPtr(ctx, stmt.target)
            if isinstance(obj, FakeObject):
                try:
                    fake_obj = FakeObject(stmt.attr, obj)
                    self.workList.append((ADD_POINT_TO, var_ptr, {fake_obj}))
                except FakeObject.NoMore:
                    pass
            if isinstance(obj, InstanceObject):
                # target <- instance.attr
                ins_attr = AttrPtr(obj, stmt.attr)
                ins_res_attr = AttrPtr(obj, FAKE_PREFIX + stmt.attr)
                self.addFlow(ins_attr, var_ptr)
                self.addFlow(ins_res_attr, var_ptr)
                class_obj = obj.type
                self.resolveAttrIfNot(class_obj, stmt.attr)
                # instance.attr <- class.$r_attr
                class_attr = AttrPtr(class_obj, FAKE_PREFIX + stmt.attr)
                self.addFlow(class_attr, ins_res_attr)

            elif isinstance(obj, ClassObject):
                self.resolveAttrIfNot(obj, stmt.attr)
                # instance.attr <- class.$r_attr
                class_attr = AttrPtr(obj, FAKE_PREFIX + stmt.attr)
                self.addFlow(class_attr, var_ptr)

            elif isinstance(obj, SuperObject):
                self.resolveAttrIfNot(obj, stmt.attr)
                # instance.attr <- class.$r_attr
                super_attr = AttrPtr(obj, FAKE_PREFIX + stmt.attr)
                self.addFlow(super_attr, var_ptr)

            else:
                attr_ptr = AttrPtr(obj, stmt.attr)
                self.addFlow(attr_ptr, var_ptr)

    def processNewClass(self, cs_stmt: 'CS_NewClass', index: int, objs: Set[Object]):
        # print(f"Process NewClass: {csStmt}")
        assert (isinstance(cs_stmt[1], NewClass))
        # ctx, stmt = cs_stmt
        mro_change = set()
        for obj in objs:
            if isinstance(obj, ClassObject):
                mro_change |= self.classHiearchy.addClassBase(CSClassObject(cs_stmt), index, obj)
        for mro in mro_change:
            class_obj = mro[0]
            if class_obj not in self.resolved_attr:
                continue
            for attr in self.resolved_attr[class_obj]:
                self.resolveAttribute(class_obj, attr, (mro, 0))

    def processCall(self, cs_stmt: 'CS_Call', objs: Set[Object]):
        # print(f"Process Call: {csStmt}")
        assert (isinstance(cs_stmt[1], Call))
        ctx, stmt = cs_stmt
        var_ptr = CSVarPtr(ctx, stmt.target)
        new_objs = set()
        for obj in objs:
            # if(isinstance(obj, FakeObject)):
            #     func = obj.getCodeBlock()
            #     cs_code_block = (emptyContextChain(), func)
            #     self.callgraph.put(csStmt, cs_code_block)
            if isinstance(obj, FunctionObject):
                func = obj.getCodeBlock()
                tail_ctx = selectContext(cs_stmt, None)
                new_ctx = *obj.ctxChain, tail_ctx
                self.matchArgParam(pos_args=[CSVarPtr(ctx, posArg) for posArg in stmt.posargs],
                                   kw_args={kw: CSVarPtr(ctx, kwarg) for kw, kwarg in stmt.kwargs.items()},
                                   pos_params=[CSVarPtr(new_ctx, param) for param in func.posargs],
                                   kw_params={kw: CSVarPtr(new_ctx, kwOnlyParam) for kw, kwOnlyParam in
                                              func.kwargs.items()},
                                   var_param=CSVarPtr(new_ctx, func.vararg) if func.vararg else None,
                                   kw_param=CSVarPtr(new_ctx, func.kwarg) if func.kwarg else None)
                ret_var = CSVarPtr(new_ctx, func.returnVariable)
                res_var = CSVarPtr(ctx, stmt.target)
                self.addFlow(ret_var, res_var)
                cs_code_block = (new_ctx, func)
                self.addReachable(cs_code_block)
                self.callgraph.put(stmt, func)

            elif isinstance(obj, InstanceMethodObject):
                func = obj.func.getCodeBlock()
                tail_ctx = selectContext(cs_stmt, obj.selfObj)
                new_ctx = *obj.func.ctxChain, tail_ctx
                pos_params = [CSVarPtr(new_ctx, param) for param in func.posargs]
                if len(pos_params) == 0:
                    # not a method, just skip
                    continue

                self.workList.append((ADD_POINT_TO, pos_params[0], {obj.selfObj}))
                del pos_params[0]
                self.matchArgParam(pos_args=[CSVarPtr(ctx, posArg) for posArg in stmt.posargs],
                                   kw_args={kw: CSVarPtr(ctx, kwarg) for kw, kwarg in stmt.kwargs.items()},
                                   pos_params=pos_params,
                                   kw_params={kw: CSVarPtr(new_ctx, kwOnlyParam) for kw, kwOnlyParam in
                                              func.kwargs.items()},
                                   var_param=CSVarPtr(new_ctx, func.vararg) if func.vararg else None,
                                   kw_param=CSVarPtr(new_ctx, func.kwarg) if func.kwarg else None)
                ret_var = CSVarPtr(new_ctx, func.returnVariable)
                res_var = CSVarPtr(ctx, stmt.target)
                self.addFlow(ret_var, res_var)
                cs_code_block = (new_ctx, func)
                self.addReachable(cs_code_block)
                self.callgraph.put(stmt, func)

            elif isinstance(obj, ClassMethodObject):
                func = obj.func.getCodeBlock()
                tail_ctx = selectContext(cs_stmt, obj.classObj)
                new_ctx = *obj.func.ctxChain, tail_ctx
                pos_params = [CSVarPtr(new_ctx, param) for param in func.posargs]

                if len(pos_params) == 0:
                    # not a method, just skip
                    continue
                self.workList.append((ADD_POINT_TO, pos_params[0], {obj.classObj}))
                del pos_params[0]
                self.matchArgParam(pos_args=[CSVarPtr(ctx, posArg) for posArg in stmt.posargs],
                                   kw_args={kw: CSVarPtr(ctx, kwarg) for kw, kwarg in stmt.kwargs.items()},
                                   pos_params=pos_params,
                                   kw_params={kw: CSVarPtr(new_ctx, kwOnlyParam) for kw, kwOnlyParam in
                                              func.kwargs.items()},
                                   var_param=CSVarPtr(new_ctx, func.vararg) if func.vararg else None,
                                   kw_param=CSVarPtr(new_ctx, func.kwarg) if func.kwarg else None)
                ret_var = CSVarPtr(new_ctx, func.returnVariable)
                res_var = CSVarPtr(ctx, stmt.target)
                self.addFlow(ret_var, res_var)
                cs_code_block = (new_ctx, func)
                self.addReachable(cs_code_block)
                self.callgraph.put(stmt, func)

            elif isinstance(obj, StaticMethodObject):
                func = obj.func.getCodeBlock()
                tail_ctx = selectContext(cs_stmt, None)
                new_ctx = *obj.func.ctxChain, tail_ctx
                self.matchArgParam(pos_args=[CSVarPtr(ctx, posArg) for posArg in stmt.posargs],
                                   kw_args={kw: CSVarPtr(ctx, kwarg) for kw, kwarg in stmt.kwargs.items()},
                                   pos_params=[CSVarPtr(new_ctx, param) for param in func.posargs],
                                   kw_params={kw: CSVarPtr(new_ctx, kwOnlyParam) for kw, kwOnlyParam in
                                              func.kwargs.items()},
                                   var_param=CSVarPtr(new_ctx, func.vararg) if func.vararg else None,
                                   kw_param=CSVarPtr(new_ctx, func.kwarg) if func.kwarg else None)
                ret_var = CSVarPtr(new_ctx, func.returnVariable)
                res_var = CSVarPtr(ctx, stmt.target)
                self.addFlow(ret_var, res_var)
                cs_code_block = (new_ctx, func)
                self.addReachable(cs_code_block)
                self.callgraph.put(stmt, func)

            elif isinstance(obj, ClassObject):
                ins_obj = CSInstanceObject(cs_stmt, obj)
                # target <- instance.attr
                ins_attr = AttrPtr(ins_obj, FAKE_PREFIX + "__init__")
                class_attr = AttrPtr(obj, FAKE_PREFIX + "__init__")
                self.addFlow(class_attr, ins_attr)
                self.resolveAttrIfNot(obj, "__init__")

                init = Variable(f"${obj}$__init__", stmt.belongsTo)
                init_ptr = CSVarPtr(ctx, init)
                self.addFlow(ins_attr, init_ptr)
                new_stmt = (ctx, Call(Variable("", stmt.belongsTo), init, stmt.posargs, stmt.kwargs, stmt.belongsTo))
                self.workList.append((BIND_STMT, new_stmt))

                new_objs.add(ins_obj)
        if new_objs:
            self.workList.append((ADD_POINT_TO, var_ptr, new_objs))

    def matchArgParam(self, /, pos_args: List[CSVarPtr],
                      kw_args: Dict[str, CSVarPtr],
                      pos_params: List[CSVarPtr],
                      kw_params: Dict[str, CSVarPtr],
                      var_param: CSVarPtr, kw_param: CSVarPtr):

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

    def processDelAttr(self, cs_stmt: 'CS_DelAttr', objs: Set[CSObject]):
        # print(f"Process DelAttr: {csStmt}")
        assert (isinstance(cs_stmt[1], DelAttr))
        ctx, stmt = cs_stmt
        attr = stmt.attr
        for obj in objs:
            if obj in self.persist_attr and attr in self.persist_attr[obj]:
                for mro, index in self.persist_attr[obj][attr]:
                    self.resolveAttribute(mro[0], attr, (mro, index + 1))
                del self.persist_attr[obj][attr]

    def processNewClassMethod(self, cs_stmt: 'CS_NewClassMethod', objs: Set[Object]):
        assert (isinstance(cs_stmt[1], NewClassMethod))
        ctx, stmt = cs_stmt
        target = CSVarPtr(ctx, stmt.target)
        new_objs = set()
        for obj in objs:
            if isinstance(obj, FunctionObject) and isinstance(stmt.belongsTo, ClassCodeBlock):
                for classObj in self.pointToSet.get(CSVarPtr(ctx, stmt.belongsTo.thisClassVariable)):
                    if isinstance(classObj, ClassObject):
                        class_method = ClassMethodObject(classObj, obj)
                        new_objs.add(class_method)
        if new_objs:
            self.workList.append((ADD_POINT_TO, target, new_objs))

    def processNewStaticMethod(self, cs_stmt: 'CS_NewStaticMethod', objs: Set[Object]):
        assert (isinstance(cs_stmt[1], NewStaticMethod))
        ctx, stmt = cs_stmt
        new_objs = set()
        target = CSVarPtr(ctx, stmt.target)
        for obj in objs:
            if isinstance(obj, FunctionObject) and isinstance(stmt.belongsTo, ClassCodeBlock):
                static_method = StaticMethodObject(obj)
                new_objs.add(static_method)
        self.workList.append((ADD_POINT_TO, target, new_objs))

    def processNewSuper_type(self, cs_stmt: 'CS_NewSuper', objs: Set[Object]):
        assert (isinstance(cs_stmt[1], NewSuper))
        ctx, stmt = cs_stmt
        new_objs = set()
        target = CSVarPtr(ctx, stmt.target)
        for obj in objs:
            if isinstance(obj, ClassObject):
                for boundObj in self.pointToSet.get(CSVarPtr(ctx, stmt.bound)):
                    new_objs.add(SuperObject(obj, boundObj))
        if new_objs:
            self.workList.append((ADD_POINT_TO, target, new_objs))

    def processNewSuper_bound(self, cs_stmt: 'CS_NewSuper', objs: Set[Object]):
        assert (isinstance(cs_stmt[1], NewSuper))
        ctx, stmt = cs_stmt
        new_objs = set()
        target = CSVarPtr(ctx, stmt.target)
        for obj in objs:
            if isinstance(obj, ClassObject) or isinstance(obj, InstanceObject):
                for typeObj in self.pointToSet.get(CSVarPtr(ctx, stmt.type)):
                    new_objs.add(SuperObject(typeObj, obj))
        if new_objs:
            self.workList.append((ADD_POINT_TO, target, new_objs))
