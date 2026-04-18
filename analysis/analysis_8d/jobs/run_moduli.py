import sys
import itertools
import json
import time
from pathlib import Path
from dataclasses import asdict

sys.path.append(str(Path(__file__).resolve().parent.parent))

from analysis_8d.services.moduli_service import (
    get_coefficients_8d,
    get_moduli_8d_info_from_components,
    get_moduli_8d_components_list,
)
from common.weight import get_fund_weights_sp_9d
from model.moduli import Moduli8DComponent
from sqlite.db_utils import (
    select_moduli_9d,
    bulk_insert_moduli_8d,
    delete_records,
)
from sqlite.entities import Moduli8d
from config.env_settings import ENV
from config.logging_config import get_logger


############
# Settings
############
debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
skip_nodes = [["8", "18"]]
log = get_logger("moduli_8d")


def main():
    # Get 9d Moduli list from database
    moduli_9d_list = select_moduli_9d()
    initial_start = time.perf_counter()
    # Iterate over each 9d Modulus
    for m9 in moduli_9d_list:
        removed_nodes = list(m9.removed_nodes)
        # Skip if the removed nodes are in the skip list
        if removed_nodes in skip_nodes:
            continue
        # Skip if the removed nodes are not in the target list
        if debug and int(m9.id) not in target_moduli_9d_ids:
            continue
        log.info("Getting moduli in 8D for removed_nodes_9d=%s", removed_nodes)
        start = time.perf_counter()
        # Get coefficients list for the 8d Modulus
        coefficients_list = get_coefficients_8d(removed_nodes)
        # Get fundamental weights for the 9d Modulus
        fund_weights_9d = get_fund_weights_sp_9d(removed_nodes)
        # Get moduli 8d components list
        moduli_8d_components_list = get_moduli_8d_components_list(
            coefficients_list, fund_weights_9d
        )
        moduli_8d_list = []
        # Iterate over each moduli tuple
        for moduli_tuple in list[tuple[Moduli8DComponent, ...]](
            itertools.product(*moduli_8d_components_list)
        ):
            delta, lie_alg, removed_nodes_8d = get_moduli_8d_info_from_components(
                moduli_tuple
            )
            moduli_8d_list.append(
                Moduli8d(
                    id=0,
                    removed_nodes=json.dumps(removed_nodes_8d),
                    moduli_9d_id=m9.id,
                    delta=json.dumps([str(e) for e in delta]),
                    gauge_group=json.dumps(asdict(lie_alg)),
                    maximal_enhanced=None,
                    cosmological_constant=None,
                    is_critical_point=None,
                    hessian=None,
                    type=None,
                )
            )
        # Delete existing records for the 9d Modulus
        delete_records(table_name="moduli_8d", conditions={"moduli_9d_id": m9.id})
        # Insert new records for the 8d Modulus
        bulk_insert_moduli_8d(items=moduli_8d_list)
        log.info("Calculation time: %.3fs", time.perf_counter() - start)
    log.info("All calculations completed successfully")
    log.info("Total calculation time: %.3fs", time.perf_counter() - initial_start)


if __name__ == "__main__":
    main()
