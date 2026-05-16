import sys
import json
from pathlib import Path
from sympy import Matrix

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.matrix_handler import SMH
from sqlite.db_connection import conn


def calculate_first_derivative(moduli_9d_id: int) -> Matrix:
    base_sql = f"""
        SELECT 
            e16.element
        FROM e16_coset_9d AS e16c9
        JOIN e16
        ON e16.id = e16c9.e16_id
        WHERE e16c9.moduli_9d_id = {moduli_9d_id}
    """
    coset_1_sql = base_sql + " AND e16c9.character = 1"
    cur = conn.execute(coset_1_sql)
    first_term = SMH.create_constant_vector(0, 16)
    for row in cur:
        first_term += SMH.create_vector_from_str_list(json.loads(row[0]))
    coset_3_sql = base_sql + " AND e16c9.character = 3"
    cur = conn.execute(coset_3_sql)
    second_term = SMH.create_constant_vector(0, 16)
    for row in cur:
        second_term += SMH.create_vector_from_str_list(json.loads(row[0]))
    return first_term - second_term
