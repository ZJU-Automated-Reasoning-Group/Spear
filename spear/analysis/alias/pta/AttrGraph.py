from collections import defaultdict
from typing import Dict, Set, Tuple

from spear.analysis.alias.pta.Pointers import Pointer, VarPtr


class AttrGraph:
    get_forward: Dict[VarPtr, Set[Tuple[VarPtr, str]]]
    # get_backward: Dict[VarPtr, Set[Tuple[VarPtr, str]]]
    # set_forward: Dict[VarPtr, Set[Tuple[VarPtr, str]]]
    set_backward: Dict[VarPtr, Set[Tuple[VarPtr, str]]]

    def __init__(self):
        self.get_forward = defaultdict(set)
        # self.get_backward = defaultdict(set)
        # self.set_forward = defaultdict(set)
        self.set_backward = defaultdict(set)

    def putGet(self, target: VarPtr, source: VarPtr, attr: str) -> bool:
        forward_tuple = (target, attr)
        # backward_tuple = (source, attr)
        if forward_tuple not in self.get_forward[source]:
            self.get_forward[source].add(forward_tuple)
            # self.get_backward[target].add(backward_tuple)
            return True
        else:
            return False

    def putSet(self, target: VarPtr, source: VarPtr, attr: str) -> bool:
        # forward_tuple = (target, attr)
        backward_tuple = (source, attr)
        if backward_tuple not in self.set_backward[target]:
            # self.set_forward[source].add(forward_tuple)
            self.set_backward[target].add(backward_tuple)
            return True
        else:
            return False

    def getTargets(self, source) -> Set[Pointer]:
        return self.get_forward[source]

    # def getSources(self, target) -> Set[Pointer]:
    #     return self.get_backward[target]

    # def setTargets(self, source) -> Set[Pointer]:
    #     return self.set_forward[source]

    def setSources(self, target) -> Set[Pointer]:
        return self.set_backward[target]
