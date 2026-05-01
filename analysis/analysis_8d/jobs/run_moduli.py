"""
8D moduli job.

Heavy work (coefficients → Cartesian product → Moduli8d rows) runs in worker processes.
SQLite and logging stay in the main process.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any

# analysis/ package root — required for child processes (spawn) to import analysis_8d.*
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_8d.services.moduli_service import (
    get_coefficients_8d,
    get_moduli_8d_info_from_components,
    get_moduli_8d_components_list,
)
from common.weight import get_fund_weights_sp_9d
from sqlite.db_utils import (
    select_moduli_9d,
    bulk_insert_moduli_8d,
    delete_records,
)
from sqlite.entities import Moduli8d
from config.env_settings import ENV
from config.logging_config import get_logger
from config.process_pool_workers import max_workers_from_env

log = get_logger("moduli_8d")

############
# Settings
############
debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
skip_nodes = [["8", "18"]]


def _compute_moduli_8d_one(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Child-process entry point: expand one moduli_9d row into many moduli_8d rows.

    No logging and no DB (main process owns log + SQLite).
    Must remain a top-level function for ProcessPoolExecutor pickling.
    """
    moduli_9d_id = int(payload["moduli_9d_id"])
    removed_nodes = payload["removed_nodes"]
    try:
        # Same pipeline as the former sequential loop, but isolated per moduli_9d_id.
        coefficients_list = get_coefficients_8d(removed_nodes)
        fund_weights_9d = get_fund_weights_sp_9d(removed_nodes)
        moduli_8d_components_list = get_moduli_8d_components_list(
            coefficients_list, fund_weights_9d
        )
        rows: list[dict[str, Any]] = []
        for moduli_tuple in itertools.product(*moduli_8d_components_list):
            delta, lie_alg, removed_nodes_8d = get_moduli_8d_info_from_components(
                moduli_tuple
            )
            # Plain dicts only — safe to pickle back to the parent.
            rows.append(
                {
                    "removed_nodes": json.dumps(removed_nodes_8d),
                    "moduli_9d_id": moduli_9d_id,
                    "delta": json.dumps([str(e) for e in delta]),
                    "gauge_group": json.dumps(asdict(lie_alg)),
                    "maximal_enhanced": None,
                    "cosmological_constant": None,
                    "is_critical_point": None,
                    "hessian": None,
                    "type": None,
                }
            )
        return {
            "ok": True,
            "moduli_9d_id": moduli_9d_id,
            "removed_nodes": removed_nodes,
            "rows": rows,
        }
    except Exception:
        return {
            "ok": False,
            "moduli_9d_id": moduli_9d_id,
            "removed_nodes": removed_nodes,
            "error": traceback.format_exc(),
        }


def _build_payloads() -> list[dict[str, Any]]:
    """Main only: read DB and apply filters; one pickle-friendly dict per moduli_9d row."""
    out: list[dict[str, Any]] = []
    moduli_9d_list = select_moduli_9d()
    for m9 in moduli_9d_list:
        removed_nodes = list(m9.removed_nodes)
        if removed_nodes in skip_nodes:
            continue
        if debug and int(m9.id) not in target_moduli_9d_ids:
            continue
        out.append({"moduli_9d_id": m9.id, "removed_nodes": removed_nodes})
    return out


def _rows_to_entities(rows: list[dict[str, Any]]) -> list[Moduli8d]:
    """Reconstruct ORM-style rows in the main process for bulk_insert_moduli_8d."""
    return [
        Moduli8d(
            id=0,
            removed_nodes=r["removed_nodes"],
            moduli_9d_id=r["moduli_9d_id"],
            delta=r["delta"],
            gauge_group=r["gauge_group"],
            maximal_enhanced=r["maximal_enhanced"],
            cosmological_constant=r["cosmological_constant"],
            is_critical_point=r["is_critical_point"],
            hessian=r["hessian"],
            type=r["type"],
        )
        for r in rows
    ]


def main() -> None:
    initial_start = time.perf_counter()
    payloads = _build_payloads()
    if not payloads:
        log.info("No moduli_9d rows to process after filters.")
        return

    workers = max_workers_from_env("MODULI_8D_WORKERS")
    log.info(
        "Starting 8D moduli build for %s moduli_9d row(s) (worker processes=%s).",
        len(payloads),
        workers,
    )

    # Parallel compute via pool; map() keeps result order aligned with payloads.
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for payload, result in zip(
            payloads, ex.map(_compute_moduli_8d_one, payloads), strict=True
        ):
            moduli_9d_id = payload["moduli_9d_id"]
            t0 = time.perf_counter()
            if not result.get("ok"):
                log.warning(
                    "Worker error moduli_9d_id=%s removed_nodes=%s\n%s",
                    moduli_9d_id,
                    result.get("removed_nodes"),
                    result.get("error", ""),
                )
                continue

            removed_nodes = result["removed_nodes"]
            rows = result["rows"]
            entities = _rows_to_entities(rows)

            log.info(
                "Computed moduli_8d rows for moduli_9d_id=%s removed_nodes_9d=%s (count=%s)",
                moduli_9d_id,
                removed_nodes,
                len(entities),
            )

            # Single-writer SQLite: only the main process runs delete + insert.
            delete_records(
                table_name="moduli_8d", conditions={"moduli_9d_id": moduli_9d_id}
            )
            bulk_insert_moduli_8d(items=entities)
            log.info(
                "Inserted %s moduli_8d rows for moduli_9d_id=%s (persist wall time %.3fs)",
                len(entities),
                moduli_9d_id,
                time.perf_counter() - t0,
            )

    log.info("All calculations completed successfully")
    log.info("Total wall time: %.3fs", time.perf_counter() - initial_start)


if __name__ == "__main__":
    # Pool must be created only when running as __main__ (required on Windows spawn).
    main()
