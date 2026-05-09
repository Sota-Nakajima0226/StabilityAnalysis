from typing import List, Tuple

from sympy import Matrix
from common.matrix_handler import SMH
from sqlite.entities import E16Coset9d, E16


def classify_e16_by_a9(
    moduli_9d_id: int, a9: Matrix, e16_roots: List[E16]
) -> Tuple[List[E16Coset9d], List[E16Coset9d], List[E16Coset9d], List[E16Coset9d]]:
    coset0 = []
    coset1 = []
    coset2 = []
    coset3 = []
    for e in e16_roots:
        pi_dot_a9 = 4 * SMH.dot_product(SMH.create_vector_from_str_list(e.element), a9)
        if pi_dot_a9 % 4 == 0:
            coset0.append(
                E16Coset9d(id=0, moduli_9d_id=moduli_9d_id, e16_id=e.id, character=0)
            )
        elif pi_dot_a9 % 4 == 1:
            coset1.append(
                E16Coset9d(id=0, moduli_9d_id=moduli_9d_id, e16_id=e.id, character=1)
            )
        elif pi_dot_a9 % 4 == 2:
            coset2.append(
                E16Coset9d(id=0, moduli_9d_id=moduli_9d_id, e16_id=e.id, character=2)
            )
        elif pi_dot_a9 % 4 == 3:
            coset3.append(
                E16Coset9d(id=0, moduli_9d_id=moduli_9d_id, e16_id=e.id, character=3)
            )
        else:
            raise Exception(
                "Invalid lattice element for pi=%s where inner product=%s with a9=%s",
                e.element,
                pi_dot_a9,
                a9,
            )
    return coset0, coset1, coset2, coset3
