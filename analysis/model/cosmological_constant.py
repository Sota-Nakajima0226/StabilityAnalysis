from dataclasses import dataclass
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from model.moduli import Moduli8D
from model.lie_algebra import SemiSimpleLieAlg


@dataclass
class CosmologicalConst8D:
    removed_nodes_9d: List[str]
    removed_nodes_8d: List[List[str]]
    moduli: Moduli8D
    semi_simple_lie_alg: SemiSimpleLieAlg
    massless_boson_count: int
    lattice_sum: float
    value: float
    is_valid: bool
    is_suppressed: bool
