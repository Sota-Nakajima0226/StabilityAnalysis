from dataclasses import dataclass
from typing import List
from sympy import Matrix


@dataclass
class FundWeightSp:
    vector: Matrix
    k: int
