import sys
import itertools
import json
from pathlib import Path
from typing import Any, List, cast
from sympy import Matrix, Rational, sqrt, floor, ceiling

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.lattice import E8_ROOTS_SP
from common.matrix_handler import SMH
from sqlite.entities import MasslessSolution9d


def solve_massless_conditions_9d(
    moduli_9d_id: int, a_1: Matrix, a_2: Matrix, g: Rational
) -> List[MasslessSolution9d]:
    result = []
    a = a_1 + a_2
    r_inverse = 1 / sqrt(g)
    floor_r_inverse = int(cast(Any, floor(r_inverse)))
    for w in range(-floor_r_inverse, floor_r_inverse + 1):
        if w == 0:  # Find non-winding solutions
            find_non_winding_solutions(
                solutions=result, moduli_9d_id=moduli_9d_id, a_1=a_1, a_2=a_2
            )
        else:
            rhs = cast(Rational, 2 - 2 * (w**2) * g)
            ranges1_o = []
            ranges1_s = []
            ranges2_o = []
            ranges2_s = []
            # Determine the bounds of each component of lattice elements
            for i in range(16):
                upper_bound = sqrt(rhs) - w * a[i]
                lower_bound = -sqrt(rhs) - w * a[i]
                # Range for the scalar conjugacy class (Python range needs int)
                lo_o = int(cast(Any, ceiling(lower_bound)))
                hi_o = int(cast(Any, floor(upper_bound)))
                range_o = range(lo_o, hi_o + 1)
                # Range for the spinor conjugacy class
                lo_s = int(cast(Any, ceiling(lower_bound - Rational(1, 2))))
                hi_s = int(cast(Any, floor(upper_bound - Rational(1, 2))))
                range_s = range(lo_s, hi_s + 1)
                if i < 8:
                    ranges1_o.append(range_o)
                    ranges1_s.append(range_s)
                else:
                    ranges2_o.append(range_o)
                    ranges2_s.append(range_s)
            # Solutions in OO class
            find_winding_solutions(
                solutions=result,
                moduli_9d_id=moduli_9d_id,
                rhs=rhs,
                a_1=a_1,
                a_2=a_2,
                w=w,
                ranges1=ranges1_o,
                ranges2=ranges2_o,
                spin1=False,
                spin2=False,
            )
            # Solutions in OS class
            find_winding_solutions(
                solutions=result,
                moduli_9d_id=moduli_9d_id,
                rhs=rhs,
                a_1=a_1,
                a_2=a_2,
                w=w,
                ranges1=ranges1_o,
                ranges2=ranges2_s,
                spin1=False,
                spin2=True,
            )
            # Solutions in SO class
            find_winding_solutions(
                solutions=result,
                moduli_9d_id=moduli_9d_id,
                rhs=rhs,
                a_1=a_1,
                a_2=a_2,
                w=w,
                ranges1=ranges1_s,
                ranges2=ranges2_o,
                spin1=True,
                spin2=False,
            )
            # Solutions in SS class
            find_winding_solutions(
                solutions=result,
                moduli_9d_id=moduli_9d_id,
                rhs=rhs,
                a_1=a_1,
                a_2=a_2,
                w=w,
                ranges1=ranges1_s,
                ranges2=ranges2_s,
                spin1=True,
                spin2=True,
            )
    return result


def find_non_winding_solutions(
    solutions: List[MasslessSolution9d], moduli_9d_id: int, a_1: Matrix, a_2: Matrix
):
    zero_vector_8d = SMH.create_constant_vector(0)
    for pi in E8_ROOTS_SP:
        pi1 = SMH.concat_vectors([pi, zero_vector_8d])
        n1 = SMH.dot_product(pi1, a_1)
        # (w, n, Pi) is a solution if n is an integer
        if isinstance(n1, Rational) and n1.q == 1:
            element = [str(0), str(int(n1))] + [str(e) for e in pi1]
            solutions.append(
                MasslessSolution9d(
                    id=0, moduli_9d_id=moduli_9d_id, element=json.dumps(element)
                )
            )
        pi2 = SMH.concat_vectors([zero_vector_8d, pi])
        n2 = SMH.dot_product(pi2, a_2)
        # (w, n, Pi) is a solution if n is an integer
        if isinstance(n2, Rational) and n2.q == 1:
            element = [str(0), str(int(n2))] + [str(e) for e in pi2]
            solutions.append(
                MasslessSolution9d(
                    id=0, moduli_9d_id=moduli_9d_id, element=json.dumps(element)
                )
            )


def find_winding_solutions(
    solutions: List[MasslessSolution9d],
    moduli_9d_id: int,
    rhs: Rational,
    a_1: Matrix,
    a_2: Matrix,
    w: int,
    ranges1: List[range],
    ranges2: List[range],
    spin1: bool,
    spin2: bool,
):
    """
    Find winding solutions by solving the conditions:
        (Pi + wA)^2 = 2 - 2(w^2R^2).
        n = w + Pi /dot A is an integer.
    """
    zero_vector = SMH.create_constant_vector(0)
    for pi1 in itertools.product(*ranges1):
        pi1 = SMH.create_vector(list(pi1))
        # Skip if pi1 is not an element of the E8 root lattice
        if sum(int(cast(Any, pi1[i, 0])) for i in range(pi1.shape[0])) % 2 != 0:
            continue
        if spin1:
            # Shift by a half vector for an element in the spinor conjugacy class
            half = cast(Rational, Rational(1, 2))
            pi1 = pi1 + SMH.create_constant_vector(half)
        pi1 = SMH.concat_vectors([pi1, zero_vector])
        v1 = pi1 + w * a_1
        lhs1 = SMH.dot_product(v1, v1)
        if lhs1 > rhs:
            # Skip if l.h.s is greater than r.h.s
            continue
        for pi2 in itertools.product(*ranges2):
            pi2 = SMH.create_vector(list(pi2))
            if sum(int(cast(Any, pi2[i, 0])) for i in range(pi2.shape[0])) % 2 != 0:
                continue
            if spin2:
                half2 = cast(Rational, Rational(1, 2))
                pi2 = pi2 + SMH.create_constant_vector(half2)
            pi2 = SMH.concat_vectors([zero_vector, pi2])
            v2 = pi2 + w * a_2
            lhs2 = SMH.dot_product(v2, v2)
            lhs = lhs1 + lhs2
            if lhs != rhs:
                continue
            n = w + SMH.dot_product(pi1, a_1) + SMH.dot_product(pi2, a_2)
            if isinstance(n, Rational) and n.q == 1:
                element = [str(int(w)), str(int(n))] + [str(e) for e in (pi1 + pi2)]
                solutions.append(
                    MasslessSolution9d(
                        id=0, moduli_9d_id=moduli_9d_id, element=json.dumps(element)
                    )
                )
