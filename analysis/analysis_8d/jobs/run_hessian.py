import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from analysis_8d.services.hessian_service import calculate_diagonalized_hessian
from common.matrix_handler import SMH
from sqlite.db_utils import (
    select_moduli_9d,
    select_joined_moduli_8d,
    bulk_update_by_id,
)
from config.env_settings import ENV
from config.logging_config import get_logger

log = get_logger("hessian_8d")

debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
# Decimal digits used when saving Hessian eigenvalues to DB.
HESSIAN_EIGENVALUE_ROUND_DIGITS = ENV.analysis_8d_hessian_eigenvalue_round_digits


def main():
    # Get the moduli_9d_ids
    moduli_9d_ids = [m9.id for m9 in select_moduli_9d()]
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        # Get the moduli_8d_list
        moduli_list = select_joined_moduli_8d(
            conditions={"moduli_9d_id": m9_id, "is_critical_point": 1}
        )
        if not moduli_list:
            continue
        # Calculate the hessian for each moduli_8d
        result_data = []
        for moduli in moduli_list:
            log.info("Calculating hessian for moduli_8d_id=%s", moduli.id)
            # Calculate the diagonalized hessian
            hessian = calculate_diagonalized_hessian(moduli=moduli)
            log.debug("hessian:\n%s", hessian)
            if not hessian.is_symmetric():
                raise Exception(f"The hessian is not a symmetric matrix: {hessian}")
            # Classify the critical point
            eigenvalues, cp_type = SMH.classify_critical_point_numerical(hessian)
            # Round the eigenvalues to the specified number of decimal digits
            rounded_eigenvalues = []
            for v in eigenvalues:
                rounded_v = round(float(v), HESSIAN_EIGENVALUE_ROUND_DIGITS)
                if rounded_v == 0.0:
                    rounded_v = 0.0
                rounded_eigenvalues.append(rounded_v)
            eigenvalues_str = [str(v) for v in rounded_eigenvalues]
            log.info("Hessian eigenvalues: %s", eigenvalues_str)
            log.info("Critical point type: %s", cp_type)
            result_data.append(
                {
                    "id": moduli.id,
                    "hessian": json.dumps(eigenvalues_str),
                    "type": str(cp_type),
                }
            )
        # Bulk update the moduli_8d records
        if result_data:
            bulk_update_by_id(table_name="moduli_8d", update_data_list=result_data)
    log.info("All Hessian calculations completed successfully")


if __name__ == "__main__":
    main()
