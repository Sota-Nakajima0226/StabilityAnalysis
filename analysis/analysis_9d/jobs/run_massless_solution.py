"""
9D massless solution job.

Heavy computation runs in worker processes; SQLite and logging stay in the main process
(see documents/massless_9d_parallel_design.md).
"""

from __future__ import annotations

import sys
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, cast

from sympy import Rational

# Repository layout: this file lives under analysis/analysis_9d/jobs/
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_9d.services.massless_solution_service import solve_massless_conditions_9d
from common.dynkin_handler import DH_E16
from common.matrix_handler import SMH
from model.lie_algebra import SemiSimpleLieAlg
from sqlite.db_utils import (
    select_moduli_9d,
    bulk_insert_massless_solution_9d,
    delete_records,
)
from sqlite.entities import MasslessSolution9d
from config.env_settings import ENV
from config.logging_config import get_logger
from config.process_pool_workers import max_workers_from_env

log = get_logger("massless_solution_9d")

############
# Settings
############
debug = ENV.analysis_9d_debug
target_moduli_9d_ids = ENV.analysis_9d_target_moduli_9d_ids
skip_nodes = [["8", "18"]]


def _compute_massless_one(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Child-process entry point: SymPy solve + validation only.

    No logging and no DB here (design: main process owns log + SQLite).
    Must stay picklable as a top-level function for ProcessPoolExecutor.
    """
    moduli_9d_id = int(payload["moduli_9d_id"])
    removed_nodes = payload["removed_nodes"]
    try:
        zero_vector_8d = SMH.create_constant_vector(0)
        a9_1_8d = SMH.create_vector_from_str_list(payload["a9"][:8])
        a9_2_8d = SMH.create_vector_from_str_list(payload["a9"][8:])
        a9_1 = SMH.concat_vectors([a9_1_8d, zero_vector_8d])
        a9_2 = SMH.concat_vectors([zero_vector_8d, a9_2_8d])
        g9 = cast(Rational, Rational(payload["g9"]))
        massless_solutions = solve_massless_conditions_9d(
            moduli_9d_id=moduli_9d_id, a_1=a9_1, a_2=a9_2, g=g9
        )
        gauge_group = SemiSimpleLieAlg(**cast(dict, payload["gauge_group"]))
        is_valid = len(massless_solutions) == DH_E16.count_nonzero_roots(
            gauge_group
        )
        # Serialize for IPC: only plain data (element is already JSON str in entities).
        rows = [
            {"moduli_9d_id": m.moduli_9d_id, "element": m.element}
            for m in massless_solutions
        ]
        return {
            "ok": True,
            "moduli_9d_id": moduli_9d_id,
            "removed_nodes": removed_nodes,
            "is_valid": is_valid,
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
    """Main only: DB read + filters; produce one pickle-friendly dict per moduli."""
    out: list[dict[str, Any]] = []
    moduli_9d_list = select_moduli_9d()
    for m9 in moduli_9d_list:
        removed_nodes = list(m9.removed_nodes)
        if removed_nodes in skip_nodes:
            continue
        if debug and int(m9.id) not in target_moduli_9d_ids:
            continue
        out.append(
            {
                "moduli_9d_id": m9.id,
                "removed_nodes": removed_nodes,
                "a9": m9.a9,
                "g9": m9.g9,
                "gauge_group": m9.gauge_group,
            }
        )
    return out


def _rows_to_entities(rows: list[dict[str, Any]]) -> list[MasslessSolution9d]:
    return [
        MasslessSolution9d(id=0, moduli_9d_id=r["moduli_9d_id"], element=r["element"])
        for r in rows
    ]


def main() -> None:
    invalid_results: list[tuple[Any, list[MasslessSolution9d]]] = []
    payloads = _build_payloads()
    if not payloads:
        log.info("No moduli_9d rows to process after filters.")
        return

    workers = max_workers_from_env("MASSLESS_9D_WORKERS")
    log.info(
        "Starting massless 9D solve for %s moduli (worker processes=%s).",
        len(payloads),
        workers,
    )

    # ProcessPoolExecutor: compute in parallel; map() returns results in payload order.
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for payload, result in zip(
            payloads, ex.map(_compute_massless_one, payloads), strict=True
        ):
            moduli_9d_id = payload["moduli_9d_id"]
            if not result.get("ok"):
                log.warning(
                    "Worker error moduli_9d_id=%s removed_nodes=%s\n%s",
                    moduli_9d_id,
                    result.get("removed_nodes"),
                    result.get("error", ""),
                )
                continue

            removed_nodes = result["removed_nodes"]
            is_valid = result["is_valid"]
            rows = result["rows"]
            entities = _rows_to_entities(rows)

            log.info(
                "Finished solve moduli_9d_id=%s removed_nodes=%s (solutions=%s, valid=%s)",
                moduli_9d_id,
                removed_nodes,
                len(entities),
                is_valid,
            )

            if is_valid:
                delete_records(
                    table_name="massless_solution_9d",
                    conditions={"moduli_9d_id": moduli_9d_id},
                )
                bulk_insert_massless_solution_9d(entities)
                log.info(
                    "Inserted %s massless solutions into DB for moduli_9d_id=%s",
                    len(entities),
                    moduli_9d_id,
                )
            else:
                log.warning("Invalid result: removed_nodes=%s", removed_nodes)
                invalid_results.append((removed_nodes, entities))

    if len(invalid_results) == 0:
        log.info("All calculations are consistent with the expected results")
    else:
        log.warning(
            "The following calculations are inconsistent with the expected results:"
        )
        for ir in invalid_results:
            log.warning("Invalid removed_nodes=%s", ir[0])


if __name__ == "__main__":
    # Required on Windows (spawn): pool must not run at import time.
    main()
