from dataclasses import dataclass, asdict
from typing import List

from model.moduli import Moduli8D
from lie_algebra import SemiSimpleLieAlg


@dataclass
class Gradient8D:
    moduli: Moduli8D
    semi_simple_lie_alg: SemiSimpleLieAlg
    gradient: List[str]
    is_critical_pont: bool
