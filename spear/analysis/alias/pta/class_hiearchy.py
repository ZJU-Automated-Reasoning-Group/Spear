import json
from collections import defaultdict
from typing import Dict, Generator, List, Set, Tuple

from spear.analysis.alias.pta import json_utils
from spear.analysis.alias.pta.objects import ClassObject, FakeObject
from spear.analysis.alias.pta.points_to_set import PointsToSet

# Here MRO mean an order in which methods are resolved, a tuple consists of class objects
MRO = Tuple[ClassObject, ...]
SubclassInfo = Tuple[ClassObject, int]


class ClassHiearchy:
    mros: Dict[ClassObject, Set[MRO]]
    subClasses: Dict[ClassObject, Set[SubclassInfo]]
    pointToSet: PointsToSet

    def __init__(self, point_to_set):
        self.mros = defaultdict(set)
        self.pointToSet = point_to_set
        self.subClasses = defaultdict(set)

    def addClass(self, class_obj: ClassObject) -> Set[MRO]:
        assert (isinstance(class_obj, ClassObject))
        if class_obj in self.mros:
            return

        bases = class_obj.bases

        for i in range(len(bases)):
            for baseObj in self.pointToSet.get(bases[i]):
                # TODO: not perfect
                if baseObj == class_obj:
                    continue
                if isinstance(baseObj, FakeObject):
                    self.addClass(baseObj)
                self.subClasses[baseObj].add((class_obj, i))

        add = self.addBaseMRO(class_obj, -1, {})

        return add

    def addClassBase(self, class_obj: ClassObject, index: int, base_obj: ClassObject) -> Set[MRO]:
        assert (isinstance(class_obj, ClassObject))
        if base_obj == class_obj:
            return set()
        if isinstance(base_obj, FakeObject):
            self.addClass(base_obj)
        self.subClasses[base_obj].add((class_obj, index))
        return self.addBaseMRO(class_obj, index, self.mros[base_obj])

    def addBaseMRO(self, class_obj: ClassObject, index: int, mro_list: Set[MRO]) -> Set[MRO]:
        assert (isinstance(class_obj, ClassObject))
        bases = class_obj.bases

        # yield mros
        def select(start: int) -> Generator[List[MRO], None, None]:
            if start == len(bases):
                yield []

            elif start == index:
                for mro in mro_list:
                    for tail in select(start + 1):
                        tail.insert(0, mro)
                        yield tail
            else:
                for obj in self.pointToSet.get(bases[start]):
                    if not isinstance(obj, ClassObject):
                        continue
                    for mro in self.mros[obj]:
                        for tail in select(start + 1):
                            tail.insert(0, mro)
                            yield tail

        add = set()
        for mros in select(0):
            order = [mro[0] for mro in mros]
            mros.append(order)
            res = self._c3(class_obj, mros)

            if res is not None and res not in self.mros[class_obj]:
                assert (res[0] == class_obj)
                add.add(res)
                self.mros[class_obj].add(res)

        if len(add) == 0:
            return set()

        all_add = add.copy()
        for subclass, index in self.subClasses[class_obj]:
            all_add |= self.addBaseMRO(subclass, index, add)
        return all_add

    # return None if it is illegal
    def _c3(self, head, mros: List) -> MRO:
        for i in range(len(mros)):
            mros[i] = list(mros[i])

        for mro in mros:
            if head in mro:
                # illegal
                return None

        res = []
        mros = [mro for mro in mros if len(mro) != 0]
        while len(mros) != 0:
            for mro in mros:
                candidate = mro[0]

                for another in mros:
                    if candidate in another[1:]:
                        break
                else:
                    res.append(candidate)
                    for another in mros:
                        if another[0] == candidate:
                            del another[0]
                    mros = [mro for mro in mros if len(mro) != 0]
                    break
            else:
                # illegal mro
                return None

        return head, *res,

    def getMROs(self, class_obj: ClassObject) -> Set[MRO]:
        return self.mros[class_obj]

    def to_json(self):
        res = defaultdict(dict)
        for cls, mros in self.mros.items():
            res[str(cls)]["MROs"] = mros
        for cls, subclasses in self.subClasses.items():
            res[str(cls)]["subclasses"] = subclasses
        return json.dumps(res, default=json_utils.default, indent=4)
