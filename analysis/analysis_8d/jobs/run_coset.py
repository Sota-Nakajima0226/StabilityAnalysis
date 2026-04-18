import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from analysis_8d.services.coset_service import classify_lattice_elements
from common.matrix_handler import SMH
from sqlite.db_utils import (
    select_moduli_9d,
    select_massless_solution_9d,
    select_moduli_8d,
    bulk_insert_coset_8d,
    delete_records,
)
from config.env_settings import ENV
from config.logging_config import get_logger

log = get_logger("coset_8d")

debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
chunk_size = ENV.analysis_8d_coset_chunk_size


def main():
    moduli_9d_ids = [m9.id for m9 in select_moduli_9d()]
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        massless_solutions_9d = select_massless_solution_9d(
            conditions={"moduli_9d_id": m9_id}
        )
        if not massless_solutions_9d:
            log.warning(
                "No massless solutions for moduli_9d_id=%s; skipping coset.", m9_id
            )
            continue
        offset = 0
        while True:
            moduli_8d_list = select_moduli_8d(
                conditions={"moduli_9d_id": m9_id},
                limit=chunk_size,
                offset=offset,
            )
            if not moduli_8d_list:
                break
            for m8 in moduli_8d_list:
                log.info("Computing coset entries for moduli_8d_id=%s", m8.id)
                delete_records(
                    table_name="coset_8d", conditions={"moduli_8d_id": m8.id}
                )
                delta = SMH.create_vector_from_str_list(m8.delta)
                coset_rows, _ = classify_lattice_elements(
                    delta, m8.id, massless_solutions_9d
                )
                if coset_rows:
                    bulk_insert_coset_8d(coset_rows)
            offset += chunk_size
            if len(moduli_8d_list) < chunk_size:
                break
    log.info("All coset calculations completed successfully")


if __name__ == "__main__":
    main()
