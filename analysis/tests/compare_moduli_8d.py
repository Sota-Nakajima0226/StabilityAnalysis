"""
Compare Mathematica reference CSV rows with SQLite moduli_8d using natural keys.

Natural key: (parent moduli_9d removed_nodes, 8d removed_nodes, delta) — not DB/MMA id.
"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

MIN_MATCHED_ROWS = int(os.getenv("REFERENCE_MIN_MATCHED_ROWS", "1"))
MIN_MATCH_RATIO = float(os.getenv("REFERENCE_MIN_MATCH_RATIO", "0.0"))

# Repo root: analysis/tests -> analysis -> repo
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_COSMO_CSV = _REPO_ROOT / "output" / "moduli_8d_cosmological_const.csv"
DEFAULT_CRITICAL_POINT_CSV = _REPO_ROOT / "output" / "moduli_8d_critical_point.csv"
DEFAULT_HESSIAN_CSV = _REPO_ROOT / "output" / "moduli_8d_hessian.csv"

HESSIAN_EIGENVALUE_LEN = 33
ZERO_EPSILON = 1e-10


def canon_json(value: str | Any) -> str:
    """Canonical JSON string for stable dict/list comparison."""
    if isinstance(value, str):
        parsed = json.loads(value)
    else:
        parsed = value
    return json.dumps(parsed, sort_keys=True, separators=(",", ":"))


def moduli_8d_key(
    parent_removed_nodes: str,
    removed_nodes_8d: str,
    delta: str,
) -> tuple[str, str, str]:
    return (
        canon_json(parent_removed_nodes),
        canon_json(removed_nodes_8d),
        canon_json(delta),
    )


def round_eigenvalue(v: float, digits: int) -> float:
    rounded = round(float(v), digits)
    if rounded == 0.0 or abs(rounded) < ZERO_EPSILON:
        return 0.0
    return rounded


def parse_hessian_eigenvalues(raw: str | None, digits: int) -> list[float]:
    if not raw:
        return []
    values = json.loads(raw)
    return [round_eigenvalue(float(x), digits) for x in values]


def normalize_critical_point_type(raw: str | None) -> str:
    if raw is None:
        return ""
    return str(raw).strip()


def csv_is_critical_point(raw: str) -> int:
    return 1 if str(raw).strip() == "1" else 0


def db_is_critical_point(raw: Any) -> int:
    if raw is None:
        return 0
    return 1 if bool(raw) else 0


@dataclass
class DbModuli8dRow:
    id: int
    moduli_9d_id: int
    parent_removed_nodes: str
    removed_nodes: str
    delta: str
    gauge_group: Optional[str]
    cosmological_constant: Optional[int]
    is_critical_point: Optional[int]
    hessian: Optional[str]
    type: Optional[str]


@dataclass
class MatchStats:
    matched: int = 0
    csv_only: int = 0
    db_only: int = 0
    mismatches: list[dict[str, Any]] = field(default_factory=list)

    def add_mismatch(
        self,
        key: tuple[str, str, str],
        field_name: str,
        csv_value: Any,
        db_value: Any,
        mma_id: Optional[str] = None,
        db_id: Optional[int] = None,
        max_samples: int = 10,
    ) -> None:
        if len(self.mismatches) >= max_samples:
            return
        self.mismatches.append(
            {
                "key": key,
                "field": field_name,
                "csv": csv_value,
                "db": db_value,
                "mma_id": mma_id,
                "db_id": db_id,
            }
        )


def build_m9_map(conn: sqlite3.Connection) -> dict[str, int]:
    """Map canonical parent removed_nodes -> moduli_9d.id."""
    cur = conn.cursor()
    cur.execute("SELECT id, removed_nodes FROM moduli_9d")
    out: dict[str, int] = {}
    for row_id, removed_nodes in cur.fetchall():
        out[canon_json(removed_nodes)] = int(row_id)
    return out


def _build_mma_m9_id_to_parent_from_files(cosmo_csv: Path) -> dict[str, str]:
    """mma moduli_9d_id -> canonical parent removed_nodes."""
    id_to_parent: dict[str, str] = {}
    with cosmo_csv.open(newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 2:
                continue
            id_to_parent[row[0]] = canon_json(row[1])

    cp_csv = cosmo_csv.parent / "moduli_8d_critical_point.csv"
    m9_to_parent: dict[str, str] = {}
    with cp_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m9_id = row["moduli_9d_id"]
            if m9_id in m9_to_parent:
                continue
            mma_row_id = row["id"]
            parent = id_to_parent.get(mma_row_id)
            if parent is not None:
                m9_to_parent[m9_id] = parent
    return m9_to_parent


def build_mma_m9_map(cosmo_csv: Path) -> dict[str, str]:
    """Mathematica moduli_9d_id (str) -> canonical parent removed_nodes."""
    return _build_mma_m9_id_to_parent_from_files(cosmo_csv)


def resolve_active_mma_m9_ids(
    mma_m9_map: dict[str, str],
    db_m9_map: dict[str, int],
    reference_moduli_9d_ids: Optional[list[int]] = None,
    reference_parent_removed_nodes: Optional[list[str]] = None,
) -> set[str]:
    """Mathematica m9 ids whose parent exists in DB and passes optional filters."""
    db_parents = set(db_m9_map.keys())
    active: set[str] = set()
    for mma_id, parent in mma_m9_map.items():
        if parent not in db_parents:
            continue
        if reference_moduli_9d_ids is not None:
            if int(mma_id) not in reference_moduli_9d_ids:
                continue
        if reference_parent_removed_nodes is not None:
            if parent not in reference_parent_removed_nodes:
                continue
        active.add(mma_id)
    return active


def build_db_m8_index(
    conn: sqlite3.Connection,
    db_m9_map: dict[str, int],
    active_parents: Optional[set[str]] = None,
    keep_keys: Optional[set[tuple[str, str, str]]] = None,
) -> dict[tuple[str, str, str], DbModuli8dRow]:
    """
    Index moduli_8d by natural key.

    If active_parents is set, only rows whose parent removed_nodes canon is in the set
    (filtered in SQL). If keep_keys is set, only those natural keys are stored — needed
    when moduli_8d is much larger than the Mathematica reference (exhaustive enumeration).
    """
    parent_to_db_m9_id = {p: i for p, i in db_m9_map.items()}
    if active_parents is not None:
        allowed_m9_ids = sorted(
            {parent_to_db_m9_id[p] for p in active_parents if p in parent_to_db_m9_id}
        )
    else:
        allowed_m9_ids = None

    sql = """
        SELECT
            m8.id,
            m8.moduli_9d_id,
            m9.removed_nodes,
            m8.removed_nodes,
            m8.delta,
            m8.gauge_group,
            m8.cosmological_constant,
            m8.is_critical_point,
            m8.hessian,
            m8.type
        FROM moduli_8d AS m8
        JOIN moduli_9d AS m9 ON m8.moduli_9d_id = m9.id
        """
    params: list[Any] = []
    if allowed_m9_ids is not None:
        if not allowed_m9_ids:
            return {}
        placeholders = ",".join("?" for _ in allowed_m9_ids)
        sql += f" WHERE m8.moduli_9d_id IN ({placeholders})"
        params.extend(allowed_m9_ids)

    cur = conn.cursor()
    cur.execute(sql, params)
    index: dict[tuple[str, str, str], DbModuli8dRow] = {}
    for row in cur:
        parent = canon_json(row[2])
        rn8 = canon_json(row[3])
        delta = canon_json(row[4])
        key = (parent, rn8, delta)
        if keep_keys is not None and key not in keep_keys:
            continue
        index[key] = DbModuli8dRow(
            id=int(row[0]),
            moduli_9d_id=int(row[1]),
            parent_removed_nodes=parent,
            removed_nodes=rn8,
            delta=delta,
            gauge_group=row[5],
            cosmological_constant=row[6],
            is_critical_point=row[7],
            hessian=row[8],
            type=row[9],
        )
    return index


def iter_cosmo_csv_rows(
    cosmo_csv: Path,
    mma_m9_map: dict[str, str],
    active_mma_m9_ids: set[str],
) -> Iterator[dict[str, Any]]:
    """Yield rows from cosmological CSV with natural key fields."""
    cp_csv = cosmo_csv.parent / "moduli_8d_critical_point.csv"
    id_to_m9: dict[str, str] = {}
    with cp_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_to_m9[row["id"]] = row["moduli_9d_id"]

    with cosmo_csv.open(newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 6:
                continue
            mma_id = row[0]
            m9_id = id_to_m9.get(mma_id)
            if m9_id is None or m9_id not in active_mma_m9_ids:
                continue
            parent = mma_m9_map[m9_id]
            yield {
                "mma_id": mma_id,
                "moduli_9d_id": m9_id,
                "parent_removed_nodes": parent,
                "removed_nodes_8d": row[2],
                "delta": row[3],
                "gauge_group": row[4],
                "cosmological_constant": int(row[5]),
                "key": moduli_8d_key(parent, row[2], row[3]),
            }


def iter_critical_point_csv_rows(
    cp_csv: Path,
    mma_m9_map: dict[str, str],
    active_mma_m9_ids: set[str],
) -> Iterator[dict[str, Any]]:
    with cp_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m9_id = row["moduli_9d_id"]
            if m9_id not in active_mma_m9_ids:
                continue
            parent = mma_m9_map[m9_id]
            yield {
                "mma_id": row["id"],
                "moduli_9d_id": m9_id,
                "parent_removed_nodes": parent,
                "removed_nodes_8d": row["removed_nodes"],
                "delta": row["delta"],
                "is_critical_point": row["is_critical_point"],
                "key": moduli_8d_key(parent, row["removed_nodes"], row["delta"]),
            }


def iter_hessian_csv_rows(
    hessian_csv: Path,
    mma_m9_map: dict[str, str],
    active_mma_m9_ids: set[str],
) -> Iterator[dict[str, Any]]:
    with hessian_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m9_id = row["moduli_9d_id"]
            if m9_id not in active_mma_m9_ids:
                continue
            parent = mma_m9_map[m9_id]
            yield {
                "mma_id": row["id"],
                "moduli_9d_id": m9_id,
                "parent_removed_nodes": parent,
                "removed_nodes_8d": row["removed_nodes"],
                "delta": row["delta"],
                "hessian": row["hessian"],
                "type": row["type"],
                "key": moduli_8d_key(parent, row["removed_nodes"], row["delta"]),
            }


def compare_field(
    stats: MatchStats,
    key: tuple[str, str, str],
    field_name: str,
    csv_value: Any,
    db_value: Any,
    mma_id: Optional[str],
    db_id: Optional[int],
    equal_fn: Callable[[Any, Any], bool],
    max_mismatch_samples: int,
) -> bool:
    if equal_fn(csv_value, db_value):
        return True
    stats.add_mismatch(
        key, field_name, csv_value, db_value, mma_id, db_id, max_mismatch_samples
    )
    return False


def compare_cosmological_constants(
    db_index: dict[tuple[str, str, str], DbModuli8dRow],
    cosmo_csv: Path,
    mma_m9_map: dict[str, str],
    active_mma_m9_ids: set[str],
    max_mismatch_samples: int = 10,
) -> MatchStats:
    stats = MatchStats()
    for csv_row in iter_cosmo_csv_rows(cosmo_csv, mma_m9_map, active_mma_m9_ids):
        key = csv_row["key"]
        db_row = db_index.get(key)
        if db_row is None:
            stats.csv_only += 1
            continue
        stats.matched += 1
        if db_row.cosmological_constant is None:
            compare_field(
                stats,
                key,
                "cosmological_constant",
                csv_row["cosmological_constant"],
                None,
                csv_row["mma_id"],
                db_row.id,
                lambda a, b: a == b,
                max_mismatch_samples,
            )
            continue
        compare_field(
            stats,
            key,
            "cosmological_constant",
            csv_row["cosmological_constant"],
            int(db_row.cosmological_constant),
            csv_row["mma_id"],
            db_row.id,
            lambda a, b: a == b,
            max_mismatch_samples,
        )
    return stats


def compare_critical_points(
    db_index: dict[tuple[str, str, str], DbModuli8dRow],
    cp_csv: Path,
    mma_m9_map: dict[str, str],
    active_mma_m9_ids: set[str],
    max_mismatch_samples: int = 10,
) -> MatchStats:
    stats = MatchStats()
    for csv_row in iter_critical_point_csv_rows(cp_csv, mma_m9_map, active_mma_m9_ids):
        key = csv_row["key"]
        db_row = db_index.get(key)
        if db_row is None:
            stats.csv_only += 1
            continue
        stats.matched += 1
        csv_cp = csv_is_critical_point(csv_row["is_critical_point"])
        db_cp = db_is_critical_point(db_row.is_critical_point)
        compare_field(
            stats,
            key,
            "is_critical_point",
            csv_cp,
            db_cp,
            csv_row["mma_id"],
            db_row.id,
            lambda a, b: a == b,
            max_mismatch_samples,
        )
    return stats


def compare_hessians(
    db_index: dict[tuple[str, str, str], DbModuli8dRow],
    hessian_csv: Path,
    mma_m9_map: dict[str, str],
    active_mma_m9_ids: set[str],
    eigenvalue_round_digits: int = 8,
    max_mismatch_samples: int = 10,
) -> MatchStats:
    stats = MatchStats()

    def eigs_equal(a: list[float], b: list[float]) -> bool:
        if len(a) != len(b):
            return False
        return all(x == y for x, y in zip(a, b))

    for csv_row in iter_hessian_csv_rows(hessian_csv, mma_m9_map, active_mma_m9_ids):
        key = csv_row["key"]
        db_row = db_index.get(key)
        if db_row is None:
            stats.csv_only += 1
            continue
        stats.matched += 1
        csv_eigs = parse_hessian_eigenvalues(
            csv_row["hessian"], eigenvalue_round_digits
        )
        db_eigs = parse_hessian_eigenvalues(db_row.hessian, eigenvalue_round_digits)
        compare_field(
            stats,
            key,
            "hessian",
            csv_eigs,
            db_eigs,
            csv_row["mma_id"],
            db_row.id,
            eigs_equal,
            max_mismatch_samples,
        )
        compare_field(
            stats,
            key,
            "type",
            normalize_critical_point_type(csv_row["type"]),
            normalize_critical_point_type(db_row.type),
            csv_row["mma_id"],
            db_row.id,
            lambda a, b: a == b,
            max_mismatch_samples,
        )
    return stats


def compute_coverage(
    db_index: dict[tuple[str, str, str], DbModuli8dRow],
    cosmo_csv: Path,
    mma_m9_map: dict[str, str],
    active_mma_m9_ids: set[str],
) -> tuple[int, int, int]:
    """Return (matched, csv_rows_in_scope, db_rows_in_scope)."""
    csv_count = 0
    matched = 0
    for csv_row in iter_cosmo_csv_rows(cosmo_csv, mma_m9_map, active_mma_m9_ids):
        csv_count += 1
        if csv_row["key"] in db_index:
            matched += 1
    db_count = len(db_index)
    return matched, csv_count, db_count


def format_mismatches(stats: MatchStats) -> str:
    if not stats.mismatches:
        return ""
    lines = ["Sample mismatches:"]
    for m in stats.mismatches:
        lines.append(
            f"  mma_id={m.get('mma_id')} db_id={m.get('db_id')} "
            f"field={m['field']} csv={m['csv']!r} db={m['db']!r}"
        )
    return "\n".join(lines)
