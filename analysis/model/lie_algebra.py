from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum


class DynkinType(str, Enum):
    A = "A"
    D = "D"
    E = "E"


@dataclass
class SimpleLieAlg:
    type: DynkinType
    rank: int


@dataclass
class SemiSimpleLieAlg:
    A: List[int] = field(default_factory=list)
    D: List[int] = field(default_factory=list)
    E: List[int] = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, SemiSimpleLieAlg):
            return NotImplemented
        # Compare without worrying about order
        return (
            sorted(self.A) == sorted(other.A)
            and sorted(self.D) == sorted(other.D)
            and sorted(self.E) == sorted(other.E)
        )


@dataclass
class DynkinInfo:
    type: DynkinType
    rank: int
    diagram: Dict[str, List[str]]
    endpoints: List[str]
    segments: List[str]
    intersections: List[str]
