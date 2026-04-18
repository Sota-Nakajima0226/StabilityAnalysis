import sys
from pathlib import Path
from typing import cast
from dataclasses import asdict

from sympy import Rational

sys.path.append(str(Path(__file__).resolve().parent.parent))

from analysis_9d.services.massless_solution_service import solve_massless_conditions_9d
from common.dynkin_handler import DH_E16
from common.json_handler import JSON_HANDLER
import common.file_path as fp
from common.matrix_handler import SMH
from model.lie_algebra import SemiSimpleLieAlg
from sqlite.db_utils import (
    select_moduli_9d,
    bulk_insert_massless_solution_9d,
    delete_records,
)
from config.env_settings import ENV
from config.logging_config import get_logger

log = get_logger("massless_solution_9d")

############
# Settings
############
debug = ENV.analysis_9d_debug
target_moduli_9d_ids = ENV.analysis_9d_massless_solution_target_moduli_9d_ids
skip_nodes = [["8", "18"]]


def main():
    fp.MASSLESS_SOLUTION_9D_DIR_PATH.mkdir(parents=True, exist_ok=True)
    invalid_results = []
    zero_vector_8d = SMH.create_constant_vector(0)
    moduli_9d_list = select_moduli_9d()
    for m9 in moduli_9d_list:
        removed_nodes = list(m9.removed_nodes)
        if removed_nodes in skip_nodes:
            continue
        if debug and int(m9.id) not in target_moduli_9d_ids:
            continue
        log.info(
            f"Solving the massless conditions in 9D for removed_nodes={removed_nodes}..."
        )
        a9_1_8d = SMH.create_vector_from_str_list(m9.a9[:8])
        a9_2_8d = SMH.create_vector_from_str_list(m9.a9[8:])
        a9_1 = SMH.concat_vectors([a9_1_8d, zero_vector_8d])
        a9_2 = SMH.concat_vectors([zero_vector_8d, a9_2_8d])
        g9 = cast(Rational, Rational(m9.g9))
        # Solve massless conditions with the moduli in 9D
        massless_solutions = solve_massless_conditions_9d(
            moduli_9d_id=m9.id, a_1=a9_1, a_2=a9_2, g=g9
        )
        # Check if the number of solutions matches the dimension of gauge group
        gauge_group = SemiSimpleLieAlg(**cast(dict, m9.gauge_group))
        is_valid = len(massless_solutions) == DH_E16.count_nonzero_roots(gauge_group)
        if is_valid:
            # Delete previous results before inserting new results
            delete_records(
                table_name="massless_solution_9d", conditions={"moduli_9d_id": m9.id}
            )
            # Insert the calculation results
            bulk_insert_massless_solution_9d(massless_solutions)
            log.info(
                "Inserted %s massless solutions into DB for moduli_9d_id=%s",
                len(massless_solutions),
                m9.id,
            )
        else:
            log.warning("Invalid result: removed_nodes=%s", m9.removed_nodes)
            invalid_results.append((m9.removed_nodes, massless_solutions))
    if len(invalid_results) == 0:
        log.info("All calculations are consistent with the expected results")
    else:
        log.warning(
            "The following calculations are inconsistent with the expected results:"
        )
        for ir in invalid_results:
            log.warning("Invalid removed_nodes=%s", ir[0])
            file_path = (
                fp.MASSLESS_SOLUTION_9D_DIR_PATH
                / "invalid_results"
                / f"{ir[0][0]}-{ir[0][1]}.json"
            )
            log.info(
                "Writing invalid result JSON: path=%s, removed_nodes=%s, count=%s",
                file_path,
                ir[0],
                len(ir[1]),
            )
            JSON_HANDLER.save_json(asdict(ir[1]), file_path)
            log.info("Wrote invalid result JSON: %s", file_path)


if __name__ == "__main__":
    main()
