from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_9d.services.hessian_service import calculate_hessian
from common.matrix_handler import SMH
from sqlite.db_utils import (
    bulk_update_by_id,
    select_moduli_9d,
)
from config.env_settings import ENV
from config.logging_config import get_logger

log = get_logger("hessian_8d")

debug = ENV.analysis_9d_debug
target_moduli_9d_ids = ENV.analysis_9d_target_moduli_9d_ids
HESSIAN_EIGENVALUE_ROUND_DIGITS = ENV.analysis_9d_hessian_eigenvalue_round_digits


def main() -> None:
    moduli_9d_ids = [
        m9.id
        for m9 in select_moduli_9d(
            conditions={"is_critical_point": 1},
            use_analysis_9d=True,
        )
    ]
    result_data: list[dict[str, Any]] = []
    failed_moduli_9d_ids: list[int] = []
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        log.info(
            "Calculating Hessian for moduli_9d_id=%s",
            m9_id,
        )
        try:
            hessian = calculate_hessian(moduli_9d_id=m9_id)
            if not hessian.is_symmetric():
                raise Exception(f"The hessian is not a symmetric matrix: {hessian}")
            eigenvalues, cp_type = SMH.classify_critical_point_numerical(hessian)
            rounded_eigenvalues = []
            print(eigenvalues)
            for v in eigenvalues:
                rounded_v = round(float(v), HESSIAN_EIGENVALUE_ROUND_DIGITS)
                if rounded_v == 0.0:
                    rounded_v = 0.0
                rounded_eigenvalues.append(rounded_v)
            eigenvalues_str = [str(v) for v in rounded_eigenvalues]
            result_data.append(
                {
                    "id": int(m9_id),
                    "hessian": json.dumps(eigenvalues_str),
                    "type": str(cp_type.value),
                }
            )
        except Exception as e:
            log.warning(
                "Error calculating Hessian for moduli_9d_id=%s: %s",
                m9_id,
                e,
            )
            failed_moduli_9d_ids.append(m9_id)

    if result_data:
        bulk_update_by_id(table_name="moduli_9d", update_data_list=result_data)
    if failed_moduli_9d_ids:
        preview = failed_moduli_9d_ids[:20]
        suffix = " ..." if len(failed_moduli_9d_ids) > len(preview) else ""
        log.warning(
            "Failed moduli_8d rows (%s): %s%s",
            len(failed_moduli_9d_ids),
            preview,
            suffix,
        )
    else:
        log.info("All Hessian calculations completed successfully")


if __name__ == "__main__":
    main()
