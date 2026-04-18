import sys
from pathlib import Path
from dataclasses import asdict

sys.path.append(str(Path(__file__).resolve().parent.parent))

from analysis_8d.services.cosmological_constant_service import get_cosmological_constant
from sqlite.db_utils import (
    select_moduli_8d,
    bulk_update_by_id,
    get_massless_states_count_from_coset_8d,
)
from config.env_settings import ENV
from config.logging_config import get_logger

log = get_logger("cosmological_const_8d")

debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
chunk_size = ENV.analysis_8d_cosmological_const_chunk_size


def main():
    offset = 0
    moduli_8d_with_suppressed_cc = []
    log.info("Counting massless states...")
    massless_states_count = get_massless_states_count_from_coset_8d()
    while True:
        # get moduli_8d
        moduli_8d_list = select_moduli_8d(limit=chunk_size, offset=offset)
        if not moduli_8d_list:
            break
        update_data_list = []
        for moduli_8d in moduli_8d_list:
            if debug and moduli_8d.moduli_9d_id not in target_moduli_9d_ids:
                continue
            log.debug("removed_nodes by moduli_8d: %s", moduli_8d.removed_nodes)
            # Get the value of the cosmological constant
            value = get_cosmological_constant(massless_states_count, moduli_8d.id)
            update_data_list.append(
                {"id": moduli_8d.id, "cosmological_constant": value}
            )
            if value == 0:
                moduli_8d.cosmological_constant = value
                moduli_8d_with_suppressed_cc.append(asdict(moduli_8d))
        # bulk update
        bulk_update_by_id(table_name="moduli_8d", update_data_list=update_data_list)
        offset += chunk_size
    log.info("All calculations completed successfully")
    if moduli_8d_with_suppressed_cc:
        log.info(
            "Moduli with suppressed cosmological constant (%s):",
            len(moduli_8d_with_suppressed_cc),
        )
        for m8 in moduli_8d_with_suppressed_cc:
            log.info("%s", m8)


if __name__ == "__main__":
    main()
