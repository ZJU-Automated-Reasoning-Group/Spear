import json
from collections import defaultdict
from typing import Dict, Set

from spear.analysis.alias.pta import json_utils
from spear.analysis.alias.pta.pointers import Pointer


class PointerFlow:
    forward: Dict[Pointer, Set[Pointer]]

    # backward: Dict[Pointer, Set[Pointer]]
    def __init__(self):
        self.forward = defaultdict(set)
        # self.backward = defaultdict(set)

    def put(self, source: Pointer, target: Pointer) -> bool:

        if target not in self.forward[source]:
            self.forward[source].add(target)
            # self.backward[target].add(source)
            return True
        else:
            return False

    def successors(self, source) -> Set[Pointer]:
        return self.forward[source]

    # def precedents(self, target) -> Set[Pointer]:
    #     return self.backward[target]

    def to_json(self):
        forward = {str(ptr): s for ptr, s in self.forward.items()}
        backward = defaultdict(set)
        for src, s in self.forward.items():
            for des in s:
                backward[str(des)].add(src)
        return json.dumps(
            {"forward": forward, "backward": backward},
            default=json_utils.default,
            indent=4)
