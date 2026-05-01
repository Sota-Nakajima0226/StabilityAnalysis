from __future__ import annotations

import sys
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_8d.services.critical_point_service import calculate_first_derivative
from sqlite.db_utils import select_moduli_9d, get_moduli_8d_ids, bulk_update_by_id
from config.env_settings import ENV
from config.logging_config import get_logger
from config.process_pool_workers import max_workers_from_env

log = get_logger("critical_point_8d")

debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
# When non-empty and debug is true, only these moduli_8d.id values are processed.
target_moduli_8d_ids = ENV.analysis_8d_target_moduli_8d_ids
chunk_size = ENV.analysis_8d_critical_point_chunk_size


def _compute_critical_point_one(moduli_8d_id: int) -> dict[str, Any]:
    """
    Child-process entry point for one moduli_8d row.

    Worker contract:
      - Success: {"ok": True, "moduli_8d_id": int, "is_critical_point": bool}
      - Failure: {"ok": False, "moduli_8d_id": int, "error": str}

    No DB writes and no logging here; main process owns both.
    """
    try:
        first_derivative = calculate_first_derivative(moduli_8d_id=moduli_8d_id)
        return {
            "ok": True,
            "moduli_8d_id": int(moduli_8d_id),
            "is_critical_point": first_derivative.norm() == 0,
        }
    except Exception:
        return {
            "ok": False,
            "moduli_8d_id": int(moduli_8d_id),
            "error": traceback.format_exc(),
        }


def main() -> None:
    workers = max_workers_from_env("CRITICAL_POINT_8D_WORKERS")
    failed_moduli_8d_ids: list[int] = []
    # Get the moduli_9d_ids
    moduli_9d_ids = [m9.id for m9 in select_moduli_9d()]
    for m9_id in moduli_9d_ids:
        if debug and m9_id not in target_moduli_9d_ids:
            continue
        # Get the moduli_8d_ids
        moduli_8d_ids = get_moduli_8d_ids(conditions={"moduli_9d_id": m9_id})
        if not moduli_8d_ids:
            continue
        if not debug:
            target_m8_ids = moduli_8d_ids
        else:
            target_m8_ids = [
                m8_id
                for m8_id in moduli_8d_ids
                if m8_id in target_moduli_8d_ids
            ]
        if not target_m8_ids:
            continue

        log.info(
            "Calculating first derivative for moduli_9d_id=%s (targets=%s, workers=%s)",
            m9_id,
            len(target_m8_ids),
            workers,
        )

        result_data: list[dict[str, Any]] = []
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for result in ex.map(
                _compute_critical_point_one, target_m8_ids
            ):
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
                        "is_critical_point": bool(result["is_critical_point"]),
                    }
                )

        if result_data:
            bulk_update_by_id(table_name="moduli_8d", update_data_list=result_data)
    log.info("All first-derivative calculations completed successfully")
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
