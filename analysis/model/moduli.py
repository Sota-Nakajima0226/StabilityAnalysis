from dataclasses import dataclass
from typing import List, Dict, Union
import sys
from pathlib import Path
from sympy import Matrix, Rational

sys.path.append(str(Path(__file__).resolve().parent))

from model.lie_algebra import SemiSimpleLieAlg, DynkinInfo


@dataclass
class Moduli8D:
    a8: List[str]
    a9: List[str]
    g9: str
    b: str
    e21: str


@dataclass
class Moduli9DInput:
    removed_nodes: List[str]
    a9_1: Matrix
    a9_2: Matrix
    g9: Rational
    lie_algebra: SemiSimpleLieAlg


@dataclass
class Moduli9DOutput:
    removed_nodes: List[str]
    a9_1: List[str]
    a9_2: List[str]
    g9: str
    lie_algebra: SemiSimpleLieAlg


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
    coefficient: Coefficient
