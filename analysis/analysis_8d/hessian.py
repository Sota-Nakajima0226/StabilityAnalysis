from sqlite3 import Cursor
import sys
import json
import sympy as sp
from pathlib import Path
from sympy import Matrix, Rational, S

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.matrix_handler import SMH
from analysis_8d.utils import get_a8_and_b_from_delta
from sqlite.db_utils import (
    select_moduli_9d,
    select_joined_moduli_8d,
    bulk_update_by_id,
)
from sqlite.db_connection import conn
from sqlite.entities import JoinedModuli8d

############
# Settings
############
# if the execution mode is debug
debug = True
# calculation targets in debug mode
target_moduli_9d_ids = [2]
# chunk size of records in moduli_8d
chunk_size = 5000


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
        a9w_half = S(Rational(w, 2) * a9)
        a8w_half = S(Rational(w, 2) * a8)
        h11 += w**2
        h1i += w * a8w_half
        h1k += w * (a9w_half + pi)
        for a in range(16):
            for b in range(16):
                hik[a, b] += a8w_half[a] * (a9w_half[b] + pi[b])
                hij[a, b] += a8w_half[a] * a8w_half[b]
                hkl[a, b] += (a9w_half[a] + pi[a]) * (a9w_half[b] + pi[b])
    h11 = Matrix([h11])
    return sp.Matrix(
        [
            [h11, h1i.T, h1k.T],
            [h1i, hij, hik],
            [h1k, hik.T, hkl],
        ]
    )


def calculate_diagonalized_hessian(moduli: JoinedModuli8d) -> Matrix:
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


def main():
    moduli_9d_ids = [m9.id for m9 in select_moduli_9d()]
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        moduli_list = select_joined_moduli_8d(
            conditions={"moduli_9d_id": m9_id, "is_critical_point": 1}
        )
        if not moduli_list:
            continue
        result_data = []
        for moduli in moduli_list:
            print(f"Calculating hessian with moduli_8d_id = {moduli.id}")
            hessian = calculate_diagonalized_hessian(moduli=moduli)
            print("hessian:")
            print(hessian)
            if not hessian.is_symmetric():
                raise Exception(f"The hessian is not a symmetric matrix: {hessian}")
            eigenvalues, cp_type = SMH.classify_critical_point(hessian)
            eigenvalues_str = {str(k): v for k, v in eigenvalues.items()}
            print("Eigenvalues of the hessian:")
            print(eigenvalues_str)
            print("Type of the critical point:")
            print(str(cp_type))
            result_data.append(
                {
                    "id": moduli.id,
                    "hessian": json.dumps(eigenvalues_str),
                    "type": str(cp_type),
                }
            )
        bulk_update_by_id(table_name="moduli_8d", update_data_list=result_data)


if __name__ == "__main__":
    main()
