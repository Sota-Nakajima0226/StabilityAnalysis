"""
8D moduli job.

For each moduli_9d background, coefficient choices are expanded into moduli_8d
rows in index ranges of the Cartesian product (same order as itertools.product).
Workers build only their assigned range. SQLite and logging stay in the main
process.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from collections import deque
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

# analysis/ package root — required for child processes (spawn) to import analysis_8d.*
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_8d.services.moduli_service import (
    get_coefficients_8d,
    get_moduli_8d_components_list,
    get_moduli_8d_info_from_components,
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
chunk_size = ENV.analysis_8d_moduli_chunk_size
skip_nodes = [["8", "18"]]


def _product_index_to_choices(index: int, sizes: list[int]) -> list[int]:
    """
    Convert a flat index in [0, prod(sizes)) into component indices, in the same
    order as itertools.product(*ranges) (last component varies fastest).
    """
    choices: list[int] = []
    rem = index
    for size in reversed(sizes):
        choices.append(rem % size)
        rem //= size
    choices.reverse()
    return choices


def _compute_moduli_8d_chunk(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Child-process entry: build moduli_8d rows for indices in [start, end).

    No logging and no DB (main process owns log + SQLite).
    Must remain a top-level function for ProcessPoolExecutor pickling.
    """
    moduli_9d_id = int(payload["moduli_9d_id"])
    start = int(payload["start"])
    end = int(payload["end"])
    try:
        components = payload["components"]
        sizes = [len(c) for c in components]
        rows: list[dict[str, Any]] = []
        for index in range(start, end):
            choices = _product_index_to_choices(index, sizes)
            moduli_tuple = tuple(
                components[i][choices[i]] for i in range(len(components))
            )
            delta, lie_alg, removed_nodes_8d = get_moduli_8d_info_from_components(
                moduli_tuple
            )
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
            "start": start,
            "end": end,
            "rows": rows,
        }
    except Exception:
        return {
            "ok": False,
            "moduli_9d_id": moduli_9d_id,
            "start": start,
            "end": end,
            "error": traceback.format_exc(),
        }


def _build_payloads() -> list[dict[str, Any]]:
    """Main only: read DB and apply filters; one dict per moduli_9d row."""
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


def _chunk_ranges(total: int) -> Iterator[tuple[int, int]]:
    start = 0
    while start < total:
        end = min(start + chunk_size, total)
        yield start, end
        start = end


def _persist_chunk(future: Future) -> int:
    result = future.result()
    if not result["ok"]:
        raise RuntimeError(
            f"Worker error moduli_9d_id={result.get('moduli_9d_id')} "
            f"[{result.get('start')}, {result.get('end')}):\n{result.get('error', '')}"
        )
    rows = result["rows"]
    if rows:
        bulk_insert_moduli_8d(items=_rows_to_entities(rows))
    return len(rows)


def _process_background(
    ex: ProcessPoolExecutor,
    moduli_9d_id: int,
    removed_nodes: list[str],
    max_in_flight: int,
) -> int:
    coefficients_list = get_coefficients_8d(removed_nodes)
    fund_weights_9d = get_fund_weights_sp_9d(removed_nodes)
    components = get_moduli_8d_components_list(coefficients_list, fund_weights_9d)
    sizes = [len(c) for c in components]
    total = 1
    for size in sizes:
        total *= size
    if not sizes:
        total = 0

    delete_records(table_name="moduli_8d", conditions={"moduli_9d_id": moduli_9d_id})
    if total == 0:
        return 0

    pending: deque[Future] = deque()
    inserted = 0
    try:
        for start, end in _chunk_ranges(total):
            payload = {
                "moduli_9d_id": moduli_9d_id,
                "components": components,
                "start": start,
                "end": end,
            }
            pending.append(ex.submit(_compute_moduli_8d_chunk, payload))
            if len(pending) >= max_in_flight:
                inserted += _persist_chunk(pending.popleft())
        while pending:
            inserted += _persist_chunk(pending.popleft())
    finally:
        for future in pending:
            future.cancel()
    return inserted


def main() -> None:
    initial_start = time.perf_counter()
    payloads = _build_payloads()
    if not payloads:
        log.info("No moduli_9d rows to process after filters.")
        return

    workers = max_workers_from_env("MODULI_8D_WORKERS")
    max_in_flight = 2 * workers
    log.info(
        "Starting 8D moduli build for %s moduli_9d row(s) "
        "(worker processes=%s, chunk_size=%s).",
        len(payloads),
        workers,
        chunk_size,
    )

    total_inserted = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for payload in payloads:
            moduli_9d_id = payload["moduli_9d_id"]
            removed_nodes = payload["removed_nodes"]
            t0 = time.perf_counter()
            try:
                count = _process_background(
                    ex, moduli_9d_id, removed_nodes, max_in_flight
                )
            except Exception:
                log.warning(
                    "Failed moduli_9d_id=%s removed_nodes=%s\n%s",
                    moduli_9d_id,
                    removed_nodes,
                    traceback.format_exc(),
                )
                continue
            total_inserted += count
            log.info(
                "Inserted %s moduli_8d rows for moduli_9d_id=%s "
                "removed_nodes_9d=%s (wall time %.3fs)",
                count,
                moduli_9d_id,
                removed_nodes,
                time.perf_counter() - t0,
            )

    log.info("All calculations completed successfully")
    log.info(
        "Total moduli_8d rows inserted: %s (wall time %.3fs)",
        total_inserted,
        time.perf_counter() - initial_start,
    )


if __name__ == "__main__":
    # Pool must be created only when running as __main__ (required on Windows spawn).
    main()
