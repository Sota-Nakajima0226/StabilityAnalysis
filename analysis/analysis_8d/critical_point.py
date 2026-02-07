import sys
import json
from pathlib import Path
from sympy import Matrix

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.matrix_handler import SMH
from sqlite.db_utils import select_moduli_9d, get_moduli_8d_ids, bulk_update_by_id
from sqlite.db_connection import conn

############
# Settings
############
# if the execution mode is debug
debug = True
# calculation targets in debug mode
target_moduli_9d_ids = [14]
# chunk size of records in moduli_8d
chunk_size = 5000


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
    print("Calculating the first term...")
    for row in cur:
        print(row[0])
        first_term += SMH.create_vector_from_str_list(json.loads(row[0]))
    coset_3_sql = base_sql + " AND c8.character = 3"
    cur = conn.execute(coset_3_sql)
    second_term = SMH.create_constant_vector(0, 18)
    print("Calculating the second term...")
    for row in cur:
        print(row[0])
        second_term += SMH.create_vector_from_str_list(json.loads(row[0]))
    print(f"first term: {first_term}")
    print(f"second term term: {second_term}")
    return first_term - second_term


def main():
    moduli_9d_ids = [m9.id for m9 in select_moduli_9d()]
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        moduli_8d_ids = get_moduli_8d_ids(conditions={"moduli_9d_id": m9_id})
        if not moduli_8d_ids:
            continue
        result_data = []
        for m8_id in moduli_8d_ids:
            if m8_id != 325743:
                continue
            print(f"Calculating first derivative with moduli_8d_id = {m8_id}")
            first_derivative = calculate_first_derivative(moduli_8d_id=m8_id)
            result_data.append(
                {"id": m8_id, "is_critical_point": first_derivative.norm() == 0}
            )
        bulk_update_by_id(table_name="moduli_8d", update_data_list=result_data)


if __name__ == "__main__":
    main()
