import sys
from pathlib import Path
from typing import Any, List, Dict, Tuple, cast
from sympy import Rational, Matrix

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from common.matrix_handler import SMH
from model.moduli import Moduli8DComponent, WilsonLine8DData
from model.massless_solution import LatticeElement9D, LatticeCoset9D
from config.logging_config import get_logger

log = get_logger("utils_8d")


def get_a8_and_b_from_delta(delta: Matrix, a9: Matrix) -> Tuple[Matrix, Rational]:
    a8 = Matrix(delta[2:, :])
    delta0 = cast(Any, delta[0, 0])
    b = delta0 - SMH.dot_product(a9, a8) / 2
    return a8, cast(Rational, Rational(b))
