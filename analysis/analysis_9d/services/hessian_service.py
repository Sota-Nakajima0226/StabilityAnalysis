from sqlite3 import Cursor
import sys
import json
from pathlib import Path
from typing import Any
from sympy import Matrix

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.matrix_handler import SMH
from sqlite.db_connection import conn


def calculate_hessian(moduli_9d_id: int) -> Matrix:
    base_sql = f"""
        SELECT 
            e16.element
        FROM e16_coset_9d AS e16c9
        JOIN e16
        ON e16.id = e16c9.e16_id
        WHERE e16c9.moduli_9d_id = {moduli_9d_id}
    """
    coset_0_sql = base_sql + " AND e16c9.character = 0"
    cur_0 = conn.execute(coset_0_sql)
    coset_2_sql = base_sql + " AND e16c9.character = 2"
    cur_2 = conn.execute(coset_2_sql)
    return get_hessian_components(cur_0) - get_hessian_components(cur_2)


def get_hessian_components(e16_elements: Cursor) -> Matrix:
    hij = SMH.create_zero_matrix(16)
    for row in e16_elements:
        element_strs = json.loads(row[0])
        pi = SMH.create_vector_from_str_list(element_strs)
        for a in range(16):
            for b in range(16):
                pia: Any = pi[a]
                pib: Any = pi[b]
                hij[a, b] += pia * pib
    return hij
