"""
Tests for the exhaustive A-series coefficient enumeration.

- Counts for A_1..A_17 match the formula in the specification (section 5.1).
- Every reduced (legacy) choice is contained in the exhaustive list.
- The product of choices over all moduli_9d backgrounds (with the same skip as
  run_moduli) equals 30,519,126. Skipped when the DB is missing.
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path

import pytest

from analysis_8d.legacy.services.moduli_service_a_reduced import (
    find_coefficients_A as find_coefficients_A_reduced,
)
from analysis_8d.services.moduli_service import (
    count_moduli_8d_candidates,
    find_coefficients_A,
)
from config.env_settings import ENV
from model.lie_algebra import DynkinInfo, DynkinType

# Same skip as analysis_8d.jobs.run_moduli
SKIP_NODES = [["8", "18"]]
EXPECTED_TOTAL_CANDIDATES = 30_519_126


def _binomial(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def expected_a_option_count(m: int) -> int:
    """m = n+1 nodes on the extended Dynkin diagram of A_n."""
    return (
        m
        + _binomial(m, 2)
        + 2 * _binomial(m, 2)
        + 3 * _binomial(m, 3)
        + _binomial(m, 4)
    )


def make_extended_a(n: int) -> DynkinInfo:
    """Extended Dynkin diagram of A_n: a cycle of m = n+1 nodes."""
    nodes = ["-1"] + [str(i) for i in range(1, n + 1)]
    m = len(nodes)
    diagram = {
        node: [nodes[(i - 1) % m], nodes[(i + 1) % m]] for i, node in enumerate(nodes)
    }
    return DynkinInfo(
        type=DynkinType.A,
        rank=n,
        diagram=diagram,
        endpoints=[],
        segments=[],
        intersections=[],
    )


def coefficient_key(c) -> tuple:
    lie = c.lie_algebra_8d
    return (
        c.order,
        tuple(sorted(c.s.items())),
        (tuple(sorted(lie.A)), tuple(sorted(lie.D)), tuple(sorted(lie.E))),
    )


@pytest.mark.parametrize("n", list(range(1, 18)))
def test_exhaustive_a_option_count_matches_formula(n: int):
    edd = make_extended_a(n)
    m = n + 1
    assert len(edd.diagram) == m
    assert len(find_coefficients_A(edd)) == expected_a_option_count(m)


@pytest.mark.parametrize("n", list(range(1, 18)))
def test_reduced_options_are_subset_of_exhaustive(n: int):
    edd = make_extended_a(n)
    exhaustive = {coefficient_key(c) for c in find_coefficients_A(edd)}
    reduced = [coefficient_key(c) for c in find_coefficients_A_reduced(edd)]
    missing = [k for k in reduced if k not in exhaustive]
    assert not missing, f"A_{n}: {len(missing)} reduced option(s) missing"


def test_total_candidates_without_insert():
    path = Path(ENV.database_path)
    if not path.is_file():
        pytest.skip(f"Database not found: {path}")
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    try:
        # Same filter as select_moduli_9d() / run_moduli.py (use_analysis_9d = 0).
        rows = conn.execute(
            "SELECT removed_nodes FROM moduli_9d WHERE use_analysis_9d = 0"
        ).fetchall()
    finally:
        conn.close()

    import json

    total = 0
    for (removed_nodes_json,) in rows:
        removed_nodes = json.loads(removed_nodes_json)
        if removed_nodes in SKIP_NODES:
            continue
        total += count_moduli_8d_candidates(removed_nodes)
    assert total == EXPECTED_TOTAL_CANDIDATES
