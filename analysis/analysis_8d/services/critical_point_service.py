import sys
import json
from pathlib import Path
from sympy import Matrix

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.matrix_handler import SMH
from sqlite.db_connection import conn


def calculate_first_derivative(moduli_8d_id: int) -> Matrix:
    base_sql = f"""
        SELECT 
            ms9.element
        FROM coset_8d AS c8
        JOIN massless_solution_9d AS ms9
        ON ms9.id = c8.massless_solution_9d_id
        WHERE c8.moduli_8d_id = {moduli_8d_id}
    """
    coset_1_sql = base_sql + " AND c8.character = 1"
    cur = conn.execute(coset_1_sql)
    first_term = SMH.create_constant_vector(0, 18)
    for row in cur:
        first_term += SMH.create_vector_from_str_list(json.loads(row[0]))
    coset_3_sql = base_sql + " AND c8.character = 3"
    cur = conn.execute(coset_3_sql)
    second_term = SMH.create_constant_vector(0, 18)
    for row in cur:
        second_term += SMH.create_vector_from_str_list(json.loads(row[0]))
    return first_term - second_term
