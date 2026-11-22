"""
Pytest fixtures for Mathematica CSV vs DB validation.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterator, Optional

import pytest

_TESTS_ROOT = Path(__file__).resolve().parent
_ANALYSIS_ROOT = _TESTS_ROOT.parent
_REPO_ROOT = _ANALYSIS_ROOT.parent
for p in (_ANALYSIS_ROOT, _TESTS_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from config.env_settings import ENV  # noqa: E402

from compare_moduli_8d import (  # noqa: E402
    DEFAULT_COSMO_CSV,
    DEFAULT_CRITICAL_POINT_CSV,
    DEFAULT_HESSIAN_CSV,
    build_db_m8_index,
    build_m9_map,
    build_mma_m9_map,
    iter_cosmo_csv_rows,
    resolve_active_mma_m9_ids,
)

# Optional filters (comma-separated)
# REFERENCE_MODULI_9D_IDS: Mathematica moduli_9d_id values, e.g. "1,3"
# REFERENCE_PARENT_REMOVED_NODES: canonical JSON parent keys (rarely set manually)


def _parse_int_list(env_name: str) -> Optional[list[int]]:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return None
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def _parse_parent_list(env_name: str) -> Optional[list[str]]:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return None
    return [x.strip() for x in raw.split("|") if x.strip()]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return _REPO_ROOT


@pytest.fixture(scope="session")
def database_path() -> Path:
    return Path(ENV.database_path)


@pytest.fixture(scope="session")
def cosmo_csv(repo_root: Path) -> Path:
    override = os.getenv("REFERENCE_COSMO_CSV", "").strip()
    if override:
        return Path(override)
    return (
        DEFAULT_COSMO_CSV
        if DEFAULT_COSMO_CSV.is_file()
        else repo_root / "output" / "moduli_8d_cosmological_const.csv"
    )


@pytest.fixture(scope="session")
def critical_point_csv(repo_root: Path) -> Path:
    override = os.getenv("REFERENCE_CRITICAL_POINT_CSV", "").strip()
    if override:
        return Path(override)
    p = DEFAULT_CRITICAL_POINT_CSV
    return p if p.is_file() else repo_root / "output" / "moduli_8d_critical_point.csv"


@pytest.fixture(scope="session")
def hessian_csv(repo_root: Path) -> Path:
    override = os.getenv("REFERENCE_HESSIAN_CSV", "").strip()
    if override:
        return Path(override)
    p = DEFAULT_HESSIAN_CSV
    return p if p.is_file() else repo_root / "output" / "moduli_8d_hessian.csv"


@pytest.fixture(scope="session")
def eigenvalue_round_digits() -> int:
    return ENV.analysis_8d_hessian_eigenvalue_round_digits


@pytest.fixture(scope="session")
def db_conn(database_path: Path) -> Iterator[sqlite3.Connection]:
    if not database_path.is_file():
        pytest.skip(f"Database not found: {database_path}")
    conn = sqlite3.connect(str(database_path))
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def reference_csvs_exist(
    cosmo_csv: Path,
    critical_point_csv: Path,
    hessian_csv: Path,
) -> None:
    missing = [
        p for p in (cosmo_csv, critical_point_csv, hessian_csv) if not p.is_file()
    ]
    if missing:
        pytest.skip(f"Reference CSV not found: {', '.join(str(m) for m in missing)}")


@pytest.fixture(scope="session")
def comparison_context(
    db_conn: sqlite3.Connection,
    cosmo_csv: Path,
    reference_csvs_exist: None,
) -> dict:
    db_m9_map = build_m9_map(db_conn)
    mma_m9_map = build_mma_m9_map(cosmo_csv)
    active_mma_m9_ids = resolve_active_mma_m9_ids(
        mma_m9_map,
        db_m9_map,
        reference_moduli_9d_ids=_parse_int_list("REFERENCE_MODULI_9D_IDS"),
        reference_parent_removed_nodes=_parse_parent_list(
            "REFERENCE_PARENT_REMOVED_NODES"
        ),
    )
    if not active_mma_m9_ids:
        pytest.skip(
            "No Mathematica moduli_9d_id shares a parent removed_nodes with DB moduli_9d"
        )
    active_parents = {mma_m9_map[mid] for mid in active_mma_m9_ids}
    # Only index DB rows that appear in the Mathematica CSV. Exhaustive moduli_8d
    # tables are too large to load entirely into memory.
    keep_keys = {
        row["key"]
        for row in iter_cosmo_csv_rows(cosmo_csv, mma_m9_map, active_mma_m9_ids)
    }
    db_index = build_db_m8_index(
        db_conn,
        db_m9_map,
        active_parents=active_parents,
        keep_keys=keep_keys,
    )
    return {
        "db_conn": db_conn,
        "cosmo_csv": cosmo_csv,
        "db_m9_map": db_m9_map,
        "mma_m9_map": mma_m9_map,
        "active_mma_m9_ids": active_mma_m9_ids,
        "active_parents": active_parents,
        "db_index": db_index,
    }
