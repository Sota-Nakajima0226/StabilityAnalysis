from dataclasses import dataclass, asdict
from typing import List, Dict
import sys
from pathlib import Path
from sympy import Matrix

sys.path.append(str(Path(__file__).resolve().parent))

from model.lie_algebra import SemiSimpleLieAlg, DynkinInfo


@dataclass
class Coefficient:
    order: int
    s: Dict[str, int]
    lie_algebra_8d: SemiSimpleLieAlg


@dataclass
class WilsonLine8DData:
    dynkin_info_9d: DynkinInfo
    kac_labels: Dict[str, int]
    coefficients: List[Coefficient]


@dataclass
class WilsonLine8D:
    removed_nodes_9d: List[str]
    data: List[WilsonLine8DData]


@dataclass
class Moduli8DComponent:
    removed_nodes_8d: List[str]
    lie_algebra_8d: SemiSimpleLieAlg
    delta: Matrix
