"""
Compare the moduli_8d results of two SQLite databases.

Rows are matched by (moduli_9d_id, delta), not by id, so that a database built by
a different enumeration can be compared with a reference. For every matched row,
cosmological_constant, is_critical_point, hessian and type are compared exactly.

- Every row of the base DB must exist in the target DB.
- Rows that only exist in the target DB are reported but not treated as errors.
- The key must be unique in each DB.

Both databases are opened read-only. Usage (from the repository root):
    python analysis/tests/compare_moduli_8d_results.py BASE_DB TARGET_DB [--moduli-9d-ids 1,3]
Exit code is 0 when there is no mismatch, no duplicate key and no missing row.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from compare_moduli_8d import canon_json

RESULT_COLUMNS = ("cosmological_constant", "is_critical_point", "hessian", "type")
MAX_EXAMPLES = 10


@dataclass
class ComparisonStats:
    base_rows: int = 0
    target_rows: int = 0
    matched: int = 0
    base_duplicates: int = 0
    target_duplicates: int = 0
    missing_in_target: int = 0
    only_in_target: int = 0
    mismatches: dict[str, int] = field(
        default_factory=lambda: {c: 0 for c in RESULT_COLUMNS}
    )
    examples: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.base_duplicates
            or self.target_duplicates
            or self.missing_in_target
            or any(self.mismatches.values())
        )


def open_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"Database not found: {path}")
    return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)


def moduli_9d_ids(conn: sqlite3.Connection) -> set[int]:
    return {r[0] for r in conn.execute("SELECT DISTINCT moduli_9d_id FROM moduli_8d")}


def load_results(
    conn: sqlite3.Connection, moduli_9d_id: int
) -> tuple[dict[str, tuple[Any, ...]], int, int]:
    """Return ({canonical delta: results}, rows, duplicate keys) for one background."""
    results: dict[str, tuple[Any, ...]] = {}
    rows = 0
    duplicates = 0
    cur = conn.execute(
        "SELECT delta, cosmological_constant, is_critical_point, hessian, type "
        "FROM moduli_8d WHERE moduli_9d_id = ?",
        (moduli_9d_id,),
    )
    for delta, *values in cur:
        rows += 1
        key = canon_json(delta)
        if key in results:
            duplicates += 1
            continue
        results[key] = tuple(values)
    return results, rows, duplicates


def compare_background(
    base: sqlite3.Connection,
    target: sqlite3.Connection,
    moduli_9d_id: int,
    stats: ComparisonStats,
) -> None:
    base_results, base_rows, base_dup = load_results(base, moduli_9d_id)
    target_results, target_rows, target_dup = load_results(target, moduli_9d_id)
    stats.base_rows += base_rows
    stats.target_rows += target_rows
    stats.base_duplicates += base_dup
    stats.target_duplicates += target_dup
    stats.only_in_target += len(target_results.keys() - base_results.keys())

    for key, base_values in base_results.items():
        target_values = target_results.get(key)
        if target_values is None:
            stats.missing_in_target += 1
            if len(stats.examples) < MAX_EXAMPLES:
                stats.examples.append(f"missing: moduli_9d_id={moduli_9d_id} {key}")
            continue
        stats.matched += 1
        for column, b, t in zip(RESULT_COLUMNS, base_values, target_values):
            if b != t:
                stats.mismatches[column] += 1
                if len(stats.examples) < MAX_EXAMPLES:
                    stats.examples.append(
                        f"{column}: moduli_9d_id={moduli_9d_id} {key} "
                        f"base={b!r} target={t!r}"
                    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the moduli_8d results of two SQLite databases."
    )
    parser.add_argument("base_db", type=Path)
    parser.add_argument("target_db", type=Path)
    parser.add_argument(
        "--moduli-9d-ids",
        default="",
        help="comma-separated moduli_9d ids (default: all ids of both DBs)",
    )
    args = parser.parse_args()

    started = time.perf_counter()
    base = open_read_only(args.base_db)
    target = open_read_only(args.target_db)
    if args.moduli_9d_ids:
        ids = sorted(int(x) for x in args.moduli_9d_ids.split(",") if x.strip())
    else:
        ids = sorted(moduli_9d_ids(base) | moduli_9d_ids(target))

    stats = ComparisonStats()
    for moduli_9d_id in ids:
        compare_background(base, target, moduli_9d_id, stats)

    print(f"base:   {args.base_db}")
    print(f"target: {args.target_db}")
    print(f"backgrounds: {len(ids)}")
    print(f"rows: base={stats.base_rows}, target={stats.target_rows}")
    print(f"matched: {stats.matched}")
    print(f"missing in target: {stats.missing_in_target}")
    print(f"only in target: {stats.only_in_target}")
    print(
        f"duplicate keys: base={stats.base_duplicates}, "
        f"target={stats.target_duplicates}"
    )
    for column in RESULT_COLUMNS:
        print(f"{column} mismatches: {stats.mismatches[column]}")
    for example in stats.examples:
        print(f"  {example}")
    print(f"result: {'OK' if stats.ok else 'NG'}")
    print(f"elapsed: {time.perf_counter() - started:.1f}s")
    return 0 if stats.ok else 1


if __name__ == "__main__":
    sys.exit(main())
