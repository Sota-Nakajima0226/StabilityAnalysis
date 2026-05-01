"""
8D coset job.

Heavy work (classify lattice elements per moduli_8d row) runs in worker processes.
SQLite and logging stay in the main process.
"""

from __future__ import annotations

import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

# analysis/ package root — required for child processes (spawn) to import analysis_8d.*
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_8d.services.coset_service import classify_lattice_elements
from common.matrix_handler import SMH
from sqlite.db_utils import (
    select_moduli_9d,
    select_massless_solution_9d,
    select_moduli_8d,
    bulk_insert_coset_8d,
    delete_records,
)
from sqlite.entities import Coset8d, MasslessSolution9d
from config.env_settings import ENV
from config.logging_config import get_logger
from config.process_pool_workers import max_workers_from_env

log = get_logger("coset_8d")

############
# Settings
############
debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
chunk_size = ENV.analysis_8d_coset_chunk_size


def _serialize_massless_solutions(
    solutions: list[MasslessSolution9d],
) -> list[dict[str, Any]]:
    """Plain dicts for pickling into worker payloads."""
    return [
        {"id": s.id, "moduli_9d_id": s.moduli_9d_id, "element": s.element}
        for s in solutions
    ]


def _compute_coset_8d_one(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Child-process entry: classify coset rows for one moduli_8d row.

    No logging and no DB (main process owns log + SQLite).
    Must remain a top-level function for ProcessPoolExecutor pickling.
    """
    moduli_8d_id = int(payload["moduli_8d_id"])
    try:
        ms_list = [
            MasslessSolution9d(
                id=int(x["id"]),
                moduli_9d_id=int(x["moduli_9d_id"]),
                element=x["element"],
            )
            for x in payload["massless_solutions_9d"]
        ]
        delta = SMH.create_vector_from_str_list(payload["delta"])
        coset_rows, _ = classify_lattice_elements(delta, moduli_8d_id, ms_list)
        rows: list[dict[str, Any]] = [
            {
                "moduli_8d_id": r.moduli_8d_id,
                "massless_solution_9d_id": r.massless_solution_9d_id,
                "character": r.character,
            }
            for r in coset_rows
        ]
        return {"ok": True, "moduli_8d_id": moduli_8d_id, "rows": rows}
    except Exception:
        return {
            "ok": False,
            "moduli_8d_id": moduli_8d_id,
            "error": traceback.format_exc(),
        }


def _rows_to_entities(rows: list[dict[str, Any]]) -> list[Coset8d]:
    """Reconstruct rows in the main process for bulk_insert_coset_8d."""
    return [
        Coset8d(
            id=0,
            moduli_8d_id=r["moduli_8d_id"],
            massless_solution_9d_id=r["massless_solution_9d_id"],
            character=int(r["character"]),
        )
        for r in rows
    ]


def main() -> None:
    initial_start = time.perf_counter()
    workers = max_workers_from_env("COSET_8D_WORKERS")
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

        ms_payload = _serialize_massless_solutions(massless_solutions_9d)
        log.info(
            "Starting coset classification for moduli_9d_id=%s (worker processes=%s).",
            m9_id,
            workers,
        )

        offset = 0
        with ProcessPoolExecutor(max_workers=workers) as ex:
            while True:
                moduli_8d_list = select_moduli_8d(
                    conditions={"moduli_9d_id": m9_id},
                    limit=chunk_size,
                    offset=offset,
                )
                if not moduli_8d_list:
                    break

                payloads: list[dict[str, Any]] = [
                    {
                        "moduli_8d_id": m8.id,
                        "delta": m8.delta,
                        "massless_solutions_9d": ms_payload,
                    }
                    for m8 in moduli_8d_list
                ]

                for payload, result in zip(
                    payloads, ex.map(_compute_coset_8d_one, payloads), strict=True
                ):
                    moduli_8d_id = int(payload["moduli_8d_id"])
                    t0 = time.perf_counter()
                    if not result.get("ok"):
                        log.warning(
                            "Worker error moduli_8d_id=%s\n%s",
                            moduli_8d_id,
                            result.get("error", ""),
                        )
                        continue

                    rows = result.get("rows") or []
                    log.info(
                        "Computed coset entries for moduli_8d_id=%s (count=%s)",
                        moduli_8d_id,
                        len(rows),
                    )

                    delete_records(
                        table_name="coset_8d", conditions={"moduli_8d_id": moduli_8d_id}
                    )
                    if rows:
                        bulk_insert_coset_8d(_rows_to_entities(rows))
                    log.info(
                        "Persisted coset_8d for moduli_8d_id=%s (wall time %.3fs)",
                        moduli_8d_id,
                        time.perf_counter() - t0,
                    )

                offset += chunk_size
                if len(moduli_8d_list) < chunk_size:
                    break

    log.info("All coset calculations completed successfully")
    log.info("Total wall time: %.3fs", time.perf_counter() - initial_start)


if __name__ == "__main__":
    main()
