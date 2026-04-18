import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from analysis_8d.services.critical_point_service import calculate_first_derivative
from sqlite.db_utils import select_moduli_9d, get_moduli_8d_ids, bulk_update_by_id
from config.env_settings import ENV
from config.logging_config import get_logger

log = get_logger("critical_point_8d")

debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
# When non-empty and debug is true, only these moduli_8d.id values are processed.
target_moduli_8d_ids = ENV.analysis_8d_target_moduli_8d_ids
chunk_size = ENV.analysis_8d_critical_point_chunk_size


def main():
    # Get the moduli_9d_ids
    moduli_9d_ids = [m9.id for m9 in select_moduli_9d()]
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        # Get the moduli_8d_ids
        moduli_8d_ids = get_moduli_8d_ids(conditions={"moduli_9d_id": m9_id})
        if not moduli_8d_ids:
            continue
        result_data = []
        for m8_id in moduli_8d_ids:
            if debug and m8_id not in target_moduli_8d_ids:
                continue
            log.info("Calculating first derivative for moduli_8d_id=%s", m8_id)
            # Calculate the first derivative
            first_derivative = calculate_first_derivative(moduli_8d_id=m8_id)
            result_data.append(
                {"id": m8_id, "is_critical_point": first_derivative.norm() == 0}
            )
        if result_data:
            # Bulk update the moduli_8d records
            bulk_update_by_id(table_name="moduli_8d", update_data_list=result_data)
    log.info("All first-derivative calculations completed successfully")


if __name__ == "__main__":
    main()
