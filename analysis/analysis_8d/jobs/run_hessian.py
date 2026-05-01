from __future__ import annotations

import json
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_8d.services.hessian_service import calculate_hessian
from common.matrix_handler import SMH
from sqlite.db_utils import (
    bulk_update_by_id,
    select_joined_moduli_8d,
    select_moduli_9d,
)
from config.env_settings import ENV
from config.logging_config import get_logger
from config.process_pool_workers import max_workers_from_env

log = get_logger("hessian_8d")

debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
# When non-empty and debug is true, only these moduli_8d.id values are processed.
target_moduli_8d_ids = ENV.analysis_8d_target_moduli_8d_ids
chunk_size = ENV.analysis_8d_hessian_chunk_size
HESSIAN_EIGENVALUE_ROUND_DIGITS = ENV.analysis_8d_hessian_eigenvalue_round_digits


def _compute_hessian_one(moduli_8d_id: int) -> dict[str, Any]:
    """
    Child-process entry point for one moduli_8d row.

    Worker contract:
      - Success: {"ok": True, "moduli_8d_id", "hessian", "type"}
      - Failure: {"ok": False, "moduli_8d_id", "error"}

    No DB writes and no logging here; main process owns both.
    """
    try:
        rows = select_joined_moduli_8d(conditions={"id": moduli_8d_id}, limit=1)
        if not rows:
            return {
                "ok": False,
                "moduli_8d_id": int(moduli_8d_id),
                "error": f"No JoinedModuli8d row for moduli_8d_id={moduli_8d_id}",
            }
        moduli = rows[0]
        hessian = calculate_hessian(moduli=moduli)
        if not hessian.is_symmetric():
            raise Exception(f"The hessian is not a symmetric matrix: {hessian}")
        eigenvalues, cp_type = SMH.classify_critical_point_numerical(hessian)
        rounded_eigenvalues = []
        for v in eigenvalues:
            rounded_v = round(float(v), HESSIAN_EIGENVALUE_ROUND_DIGITS)
            if rounded_v == 0.0:
                rounded_v = 0.0
            rounded_eigenvalues.append(rounded_v)
        eigenvalues_str = [str(v) for v in rounded_eigenvalues]
        return {
            "ok": True,
            "moduli_8d_id": int(moduli_8d_id),
            "hessian": json.dumps(eigenvalues_str),
            "type": str(cp_type),
        }
    except Exception:
        return {
            "ok": False,
            "moduli_8d_id": int(moduli_8d_id),
            "error": traceback.format_exc(),
        }


def main() -> None:
    workers = max_workers_from_env("HESSIAN_8D_WORKERS")
    failed_moduli_8d_ids: list[int] = []
    moduli_9d_ids = [m9.id for m9 in select_moduli_9d()]
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        moduli_list = select_joined_moduli_8d(
            conditions={"moduli_9d_id": m9_id, "is_critical_point": 1}
        )
        if not moduli_list:
            continue
        if not debug:
            target_m8_ids = [m.id for m in moduli_list]
        else:
            target_m8_ids = [
                m.id for m in moduli_list if m.id in target_moduli_8d_ids
            ]
        if not target_m8_ids:
            continue

        log.info(
            "Calculating Hessian for moduli_9d_id=%s (targets=%s, workers=%s)",
            m9_id,
            len(target_m8_ids),
            workers,
        )

        result_data: list[dict[str, Any]] = []
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for result in ex.map(_compute_hessian_one, target_m8_ids):
                if not result.get("ok"):
                    failed_id = int(result.get("moduli_8d_id", -1))
                    failed_moduli_8d_ids.append(failed_id)
                    log.warning(
                        "Worker error moduli_8d_id=%s\n%s",
                        failed_id,
                        result.get("error", ""),
                    )
                    continue
                result_data.append(
                    {
                        "id": int(result["moduli_8d_id"]),
                        "hessian": str(result["hessian"]),
                        "type": str(result["type"]),
                    }
                )
                if len(result_data) >= chunk_size:
                    bulk_update_by_id(
                        table_name="moduli_8d", update_data_list=result_data
                    )
                    result_data.clear()

        if result_data:
            bulk_update_by_id(table_name="moduli_8d", update_data_list=result_data)

    log.info("All Hessian calculations completed successfully")
    if failed_moduli_8d_ids:
        preview = failed_moduli_8d_ids[:20]
        suffix = " ..." if len(failed_moduli_8d_ids) > len(preview) else ""
        log.warning(
            "Failed moduli_8d rows (%s): %s%s",
            len(failed_moduli_8d_ids),
            preview,
            suffix,
        )


if __name__ == "__main__":
    main()
