from dataclasses import dataclass
from typing import List

from model.moduli import Moduli9DOutput


@dataclass
class LatticeElement9D:
    w: int
    n: int
    pi: List[str]


@dataclass
class LatticeElement8D:
    w9: int
    n9: int
    w8: int
    n8: int
    pi: List[str]


@dataclass
class MasslessSolution9D:
    moduli: Moduli9DOutput
    count_solutions: int
    is_valid: bool
    solutions: List[LatticeElement9D]


@dataclass
class LatticeCoset9D:
    character: int
    count: int
    elements: List[LatticeElement9D]
