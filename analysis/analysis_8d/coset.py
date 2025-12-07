import sys
from pathlib import Path
from typing import List, Tuple
from sympy import Matrix, S

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.matrix_handler import SMH
from common.dynkin_handler import DH_E16
from model.lie_algebra import SemiSimpleLieAlg
from sqlite.db_utils import (
    select_moduli_9d,
    select_massless_solution_9d,
    select_moduli_8d,
    bulk_insert_coset_8d,
    delete_records,
)
from sqlite.entities import Coset8d, MasslessSolution9d

############
# Settings
############
# if the execution mode is debug
debug = False
# calculation targets in debug mode
target_moduli_9d_ids = [2]
# chunk size of records in moduli_8d
chunk_size = 5000


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
        inner_product = 4 * S(SMH.dot_product(delta, e))
        if inner_product.q != 1:
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
        print(f"There are invalid elements.")
        print(f"moduli_8d_id: {moduli_8d_id}")
        print("lattice elements:")
        for s in invalid_solutions:
            print(s)
        raise Exception(f"Invalid elements exist")
    return result, coset_0_count


def main():
    moduli_9d_ids = [m9.id for m9 in select_moduli_9d()]
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        print(f"Calculating coset with moduli_9d_id={m9_id}")
        massless_solution_9d = select_massless_solution_9d(
            conditions={"moduli_9d_id": m9_id}
        )
        print(f"length of massless_solutions: {len(massless_solution_9d)}")
        offset = 0
        while True:
            moduli_8d_list = select_moduli_8d(
                conditions={"moduli_9d_id": m9_id}, limit=chunk_size, offset=offset
            )
            if not moduli_8d_list:
                break
            for moduli_8d in moduli_8d_list:
                print(f"removed nodes by moduli_8d: {moduli_8d.removed_nodes}")
                delta_18d = SMH.create_vector_from_str_list(moduli_8d.delta)
                cosets_8d, coset_0_count = classify_lattice_elements(
                    delta=delta_18d,
                    moduli_8d_id=moduli_8d.id,
                    massless_solutions_9d=massless_solution_9d,
                )
                dim_gauge_group = DH_E16.count_nonzero_roots(
                    SemiSimpleLieAlg(**moduli_8d.gauge_group)
                )
                if coset_0_count != dim_gauge_group:
                    print(
                        f"Dimension of gauge group {moduli_8d.gauge_group}: {dim_gauge_group}"
                    )
                    print(f"The number of coset_0: {coset_0_count}")
                    raise Exception("Mismatch massless boson count")
                delete_records(
                    table_name="coset_8d", conditions={"moduli_8d_id": moduli_8d.id}
                )
                bulk_insert_coset_8d(cosets_8d)
            offset += chunk_size
    print("All calculations completed successfully")


if __name__ == "__main__":
    main()
