import sys
from pathlib import Path
from typing import List, Tuple
from sympy.core.numbers import Rational
from sympy.matrices import Matrix

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.matrix_handler import SMH
from sqlite.entities import Coset8d, MasslessSolution9d


def classify_lattice_elements(
    delta: Matrix,
    moduli_8d_id: int,
    massless_solutions_9d: List[MasslessSolution9d],
) -> Tuple[List[Coset8d], int]:
    result = []
    invalid_solutions = []
    coset_0_count = 0
    for ms9 in massless_solutions_9d:
        e = SMH.create_vector_from_str_list(ms9.element)
        inner_product = 4 * SMH.dot_product(delta, e)
        if not isinstance(inner_product, Rational) or inner_product.q != 1:
            invalid_solutions.append(e)
            continue
        c = inner_product % 4
        if c == 0:
            coset_0_count += 1
        result.append(
            Coset8d(
                id=0,
                moduli_8d_id=moduli_8d_id,
                massless_solution_9d_id=ms9.id,
                character=int(c),
            )
        )
    if invalid_solutions:
        raise Exception("Invalid lattice elements for moduli_8d_id=%s", moduli_8d_id)
    return result, coset_0_count
