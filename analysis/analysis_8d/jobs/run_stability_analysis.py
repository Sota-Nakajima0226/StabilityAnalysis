"""
8D stability analysis job: cosmological constant, critical points and Hessian.

For each moduli_9d background, the massless solutions are read once and the
moduli_8d rows are analyzed chunk by chunk in worker processes with exact integer
arithmetic. Every row of the background is recomputed and overwritten.
SQLite and logging stay in the main process.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from collections import deque
from concurrent.futures import Future, ProcessPoolExecutor
from pathlib import Path
from typing import Any, Iterator

# analysis/ package root — required for child processes (spawn) to import analysis_8d.*
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_8d.services.stability_analysis_service import (
    BackgroundLattice,
    analyze_candidates,
    prepare_background,
)
from sqlite.db_utils import (
    bulk_update_by_id,
    select_massless_solution_9d,
    select_moduli_8d_delta_chunk,
    select_moduli_9d,
)
from sqlite.entities import Moduli9d
from config.env_settings import ENV
from config.logging_config import get_logger
from config.process_pool_workers import max_workers_from_env

log = get_logger("stability_analysis_8d")

############
# Settings
############
debug = ENV.analysis_8d_debug
target_moduli_9d_ids = ENV.analysis_8d_target_moduli_9d_ids
chunk_size = ENV.analysis_8d_stability_chunk_size
round_digits = ENV.analysis_8d_hessian_eigenvalue_round_digits


def _analyze_chunk(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Child-process entry: analyze one chunk of moduli_8d rows.
    No logging and no DB (main process owns log + SQLite).
    Must remain a top-level function for ProcessPoolExecutor pickling.
    """
    try:
        rows = analyze_candidates(
            background=payload["background"],
            moduli_8d_ids=payload["ids"],
            deltas=[json.loads(d) for d in payload["deltas"]],
            round_digits=payload["round_digits"],
        )
        return {"ok": True, "rows": rows}
    except Exception:
        return {"ok": False, "error": traceback.format_exc()}


def _iter_delta_chunks(moduli_9d_id: int) -> Iterator[list[tuple[int, str]]]:
    after_id = 0
    while True:
        chunk = select_moduli_8d_delta_chunk(moduli_9d_id, after_id, chunk_size)
        if not chunk:
            return
        yield chunk
        if len(chunk) < chunk_size:
            return
        after_id = chunk[-1][0]


def _persist(future: Future) -> tuple[int, int]:
    """Write one chunk result; return (candidates, critical points)."""
    result = future.result()
    if not result["ok"]:
        raise RuntimeError(result["error"])
    rows = result["rows"]
    if rows:
        bulk_update_by_id(table_name="moduli_8d", update_data_list=rows)
    return len(rows), sum(r["is_critical_point"] for r in rows)


def _analyze_background(
    ex: ProcessPoolExecutor, background: BackgroundLattice, max_in_flight: int
) -> tuple[int, int]:
    """Analyze every moduli_8d row of one background; return (candidates, critical)."""
    pending: deque[Future] = deque()
    n_candidates = 0
    n_critical = 0
    try:
        for chunk in _iter_delta_chunks(background.moduli_9d_id):
            payload = {
                "background": background,
                "ids": [row[0] for row in chunk],
                "deltas": [row[1] for row in chunk],
                "round_digits": round_digits,
            }
            pending.append(ex.submit(_analyze_chunk, payload))
            if len(pending) >= max_in_flight:
                c, k = _persist(pending.popleft())
                n_candidates += c
                n_critical += k
        while pending:
            c, k = _persist(pending.popleft())
            n_candidates += c
            n_critical += k
    finally:
        for future in pending:
            future.cancel()
    return n_candidates, n_critical


def _target_backgrounds() -> list[Moduli9d]:
    backgrounds = select_moduli_9d()
    if debug:
        backgrounds = [m9 for m9 in backgrounds if m9.id in target_moduli_9d_ids]
    return backgrounds


def main() -> None:
    initial_start = time.perf_counter()
    workers = max_workers_from_env("STABILITY_8D_WORKERS")
    max_in_flight = 2 * workers
    failed_moduli_9d_ids: list[int] = []
    total_candidates = 0
    total_critical = 0

    with ProcessPoolExecutor(max_workers=workers) as ex:
        for m9 in _target_backgrounds():
            t0 = time.perf_counter()
            massless_solutions = select_massless_solution_9d(
                conditions={"moduli_9d_id": m9.id}
            )
            if not massless_solutions:
                log.warning(
                    "No massless solutions for moduli_9d_id=%s; skipping.", m9.id
                )
                continue
            try:
                background = prepare_background(
                    moduli_9d_id=m9.id,
                    massless_solutions=[s.element for s in massless_solutions],
                    a9=m9.a9,
                )
                n_candidates, n_critical = _analyze_background(
                    ex, background, max_in_flight
                )
            except Exception:
                failed_moduli_9d_ids.append(m9.id)
                log.error(
                    "Stability analysis failed for moduli_9d_id=%s\n%s",
                    m9.id,
                    traceback.format_exc(),
                )
                continue
            total_candidates += n_candidates
            total_critical += n_critical
            log.info(
                "moduli_9d_id=%s: candidates=%s, critical points=%s, "
                "massless solutions=%s, wall time %.3fs",
                m9.id,
                n_candidates,
                n_critical,
                len(massless_solutions),
                time.perf_counter() - t0,
            )

    log.info(
        "Stability analysis completed: candidates=%s, critical points=%s, workers=%s",
        total_candidates,
        total_critical,
        workers,
    )
    if failed_moduli_9d_ids:
        log.warning("Failed moduli_9d_id values: %s", failed_moduli_9d_ids)
    log.info("Total wall time: %.3fs", time.perf_counter() - initial_start)


if __name__ == "__main__":
    main()
