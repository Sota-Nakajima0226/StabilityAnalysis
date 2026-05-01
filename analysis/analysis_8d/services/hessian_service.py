from sqlite3 import Cursor
import sys
import json
import sympy as sp
from pathlib import Path
from typing import Any, cast, Tuple
from sympy import Matrix, Rational

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.matrix_handler import SMH
from analysis_8d.utils import get_a8_and_b_from_delta
from sqlite.db_connection import conn
from sqlite.entities import JoinedModuli8d


def get_hessian_components(massless_solutions_9d: Cursor, a9: Matrix, a8: Matrix):
    h11 = 0
    h1i = SMH.create_constant_vector(0, 16)
    h1k = SMH.create_constant_vector(0, 16)
    hik = SMH.create_zero_matrix(16)
    hij = SMH.create_zero_matrix(16)
    hkl = SMH.create_zero_matrix(16)
    for row in massless_solutions_9d:
        ms_list = json.loads(row[0])
        w = int(ms_list[0])
        pi = SMH.create_vector_from_str_list(ms_list[-16:])
        a9w_half = cast(Matrix, Rational(w, 2) * a9)
        a8w_half = cast(Matrix, Rational(w, 2) * a8)
        h11 += w**2
        h1i += w * a8w_half
        h1k += w * (a9w_half + pi)
        for a in range(16):
            for b in range(16):
                # SymPy Matrix indexing is imprecise in stubs; use Any for scalars.
                a8a: Any = a8w_half[a]
                a8b: Any = a8w_half[b]
                a9a: Any = a9w_half[a]
                a9b: Any = a9w_half[b]
                pia: Any = pi[a]
                pib: Any = pi[b]
                hik[a, b] += a8a * (a9b + pib)
                hij[a, b] += a8a * a8b
                hkl[a, b] += (a9a + pia) * (a9b + pib)
    h11 = Matrix([h11])
    return sp.Matrix(
        [
            [h11, h1i.T, h1k.T],
            [h1i, hij, hik],
            [h1k, hik.T, hkl],
        ]
    )


def calculate_hessian(moduli: JoinedModuli8d) -> Matrix:
    base_sql = f"""
        SELECT 
            ms9.element
        FROM coset_8d AS c8
        JOIN massless_solution_9d AS ms9
        ON ms9.id = c8.massless_solution_9d_id
        WHERE c8.moduli_8d_id = {moduli.id}
    """
    coset_0_sql = base_sql + " AND c8.character = 0"
    cur_0 = conn.execute(coset_0_sql)
    coset_2_sql = base_sql + " AND c8.character = 2"
    cur_2 = conn.execute(coset_2_sql)
    a9 = SMH.create_vector(moduli.a9)
    a8, _ = get_a8_and_b_from_delta(delta=SMH.create_vector(moduli.delta), a9=a9)
    return get_hessian_components(
        massless_solutions_9d=cur_0, a8=a8, a9=a9
    ) - get_hessian_components(massless_solutions_9d=cur_2, a8=a8, a9=a9)


def get_a8_and_b_from_delta(delta: Matrix, a9: Matrix) -> Tuple[Matrix, Rational]:
    a8 = Matrix(delta[2:, :])
    delta0 = cast(Any, delta[0, 0])
    b = delta0 - SMH.dot_product(a9, a8) / 2
    return a8, cast(Rational, Rational(b))
