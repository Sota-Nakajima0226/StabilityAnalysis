"""
Unit tests of the integer (NumPy) 8D calculations against the legacy SymPy
implementation.

Tests marked with the `ro_conn` fixture read the DB in `DATABASE_PATH` (read-only)
and are skipped when it does not exist. The legacy first derivative and Hessian
services open the DB on import, so they are imported inside those tests only.
"""

from __future__ import annotations

import json
import random
import sqlite3
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from analysis_8d.legacy.services.coset_service import classify_lattice_elements
from analysis_8d.services.integer_lattice_service import (
    classify_characters,
    cosmological_constants,
    first_derivatives,
    hessian,
    to_scaled_int_matrix,
)
from analysis_8d.services.stability_analysis_service import (
    analyze_candidates,
    prepare_background,
)
from common.matrix_handler import SMH
from config.env_settings import ENV
from sqlite.entities import JoinedModuli8d, MasslessSolution9d

# Small backgrounds of the current DB: 93 candidates / 306 solutions and
# 280 candidates / 544 solutions.
DB_BACKGROUNDS = [35, 25]
LEGACY_SAMPLE_BACKGROUND = 35
ROUND_DIGITS = ENV.analysis_8d_hessian_eigenvalue_round_digits


def _random_half_integer_vectors(rng: random.Random, n: int) -> list[list[str]]:
    return [[str(Fraction(rng.randint(-4, 4), 2)) for _ in range(18)] for _ in range(n)]


############
# Pure functions (no DB)
############
def test_to_scaled_int_matrix_is_exact():
    rows = [["1/2", "-3/4", "2"], ["0", "5/6", "-1"], [Fraction(-1, 3), 4, "2/4"]]
    matrix, den = to_scaled_int_matrix(rows)
    assert den == 12
    assert matrix.dtype == np.int64
    for i, row in enumerate(rows):
        for j, x in enumerate(row):
            assert Fraction(int(matrix[i, j]), den) == Fraction(x)


@pytest.mark.parametrize("value", ["0.5", "1/0", "1/-2", "a"])
def test_to_scaled_int_matrix_rejects_invalid_strings(value):
    with pytest.raises((ValueError, ZeroDivisionError)):
        to_scaled_int_matrix([[value]])


@pytest.mark.parametrize("value", [str(2**62), str(-(2**62)), str(2**63), "1/3"])
def test_to_scaled_int_matrix_rejects_overflow(value):
    rows = [[value, str(2**61)]] if value == "1/3" else [[value]]
    with pytest.raises(OverflowError):
        to_scaled_int_matrix(rows)


def test_classify_characters_matches_legacy():
    rng = random.Random(0)
    element_rows = _random_half_integer_vectors(rng, 40)
    delta_rows = _random_half_integer_vectors(rng, 5)
    elements, e_den = to_scaled_int_matrix(element_rows)
    deltas, d_den = to_scaled_int_matrix(delta_rows)
    characters = classify_characters(deltas, d_den, elements, e_den)

    solutions = [
        MasslessSolution9d(id=j, moduli_9d_id=0, element=e)
        for j, e in enumerate(element_rows)
    ]
    for k, delta in enumerate(delta_rows):
        legacy, _ = classify_lattice_elements(
            SMH.create_vector_from_str_list(delta), k, solutions
        )
        assert [c.character for c in legacy] == characters[k].tolist()


def test_classify_characters_rejects_non_integer_products():
    deltas, d_den = to_scaled_int_matrix([["1/3"] + ["0"] * 17])
    elements, e_den = to_scaled_int_matrix([["1"] + ["0"] * 17])
    with pytest.raises(ValueError):
        classify_characters(deltas, d_den, elements, e_den)


def test_classify_characters_rejects_overflow():
    deltas = np.full((1, 18), 2**40, dtype=np.int64)
    elements = np.full((1, 18), 2**20, dtype=np.int64)
    with pytest.raises(OverflowError):
        classify_characters(deltas, 1, elements, 1)


def test_cosmological_constants_and_first_derivatives():
    rng = random.Random(1)
    element_rows = _random_half_integer_vectors(rng, 30)
    elements, e_den = to_scaled_int_matrix(element_rows)
    characters = np.array(
        [[rng.randint(0, 3) for _ in element_rows] for _ in range(4)], dtype=np.int8
    )
    cc = cosmological_constants(characters)
    fd = first_derivatives(characters, elements)
    for k, chars in enumerate(characters):
        assert cc[k] == 24 + int((chars == 0).sum()) - int((chars == 2).sum())
        expected = [Fraction(0)] * 18
        for c, e in zip(chars, element_rows):
            sign = {1: 1, 3: -1}.get(int(c), 0)
            expected = [x + sign * Fraction(y) for x, y in zip(expected, e)]
        assert [Fraction(int(v), e_den) for v in fd[k]] == expected


############
# Registered data (read-only DB)
############
@pytest.fixture(scope="module")
def ro_conn():
    path = Path(ENV.database_path)
    if not path.is_file():
        pytest.skip(f"Database not found: {path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    yield conn
    conn.close()


def _load_background(conn: sqlite3.Connection, moduli_9d_id: int) -> dict:
    row = conn.execute(
        "SELECT a9 FROM moduli_9d WHERE id = ?", (moduli_9d_id,)
    ).fetchone()
    if row is None:
        pytest.skip(f"moduli_9d id={moduli_9d_id} is not in the DB")
    solutions = [
        json.loads(r[0])
        for r in conn.execute(
            "SELECT element FROM massless_solution_9d WHERE moduli_9d_id = ? "
            "ORDER BY id",
            (moduli_9d_id,),
        )
    ]
    candidates = [
        dict(
            id=r[0],
            delta=json.loads(r[1]),
            cosmological_constant=r[2],
            is_critical_point=r[3],
            hessian=r[4],
            type=r[5],
        )
        for r in conn.execute(
            "SELECT id, delta, cosmological_constant, is_critical_point, hessian, "
            "type FROM moduli_8d WHERE moduli_9d_id = ? ORDER BY id",
            (moduli_9d_id,),
        )
    ]
    if not solutions or not candidates:
        pytest.skip(f"No data for moduli_9d id={moduli_9d_id}")
    return dict(a9=json.loads(row[0]), solutions=solutions, candidates=candidates)


@pytest.mark.parametrize("moduli_9d_id", DB_BACKGROUNDS)
def test_analyze_candidates_matches_legacy_results(ro_conn, moduli_9d_id):
    """The DB values were written by the legacy SymPy jobs."""
    data = _load_background(ro_conn, moduli_9d_id)
    background = prepare_background(moduli_9d_id, data["solutions"], data["a9"])
    candidates = data["candidates"]
    rows = analyze_candidates(
        background,
        [c["id"] for c in candidates],
        [c["delta"] for c in candidates],
        ROUND_DIGITS,
    )
    keys = ["id", "cosmological_constant", "is_critical_point", "hessian", "type"]
    assert [{k: r[k] for k in keys} for r in rows] == [
        {k: c[k] for k in keys} for c in candidates
    ]


def test_characters_match_coset_8d(ro_conn):
    data = _load_background(ro_conn, LEGACY_SAMPLE_BACKGROUND)
    solution_ids = [
        r[0]
        for r in ro_conn.execute(
            "SELECT id FROM massless_solution_9d WHERE moduli_9d_id = ? ORDER BY id",
            (LEGACY_SAMPLE_BACKGROUND,),
        )
    ]
    elements, e_den = to_scaled_int_matrix(data["solutions"])
    deltas, d_den = to_scaled_int_matrix([c["delta"] for c in data["candidates"]])
    characters = classify_characters(deltas, d_den, elements, e_den)
    for k, c in enumerate(data["candidates"]):
        stored = dict(
            ro_conn.execute(
                "SELECT massless_solution_9d_id, character FROM coset_8d "
                "WHERE moduli_8d_id = ?",
                (c["id"],),
            ).fetchall()
        )
        if not stored:
            pytest.skip("coset_8d is empty for this background")
        assert [stored[s] for s in solution_ids] == characters[k].tolist()


def test_first_derivative_and_hessian_match_legacy(ro_conn):
    from analysis_8d.legacy.services.critical_point_service import (
        calculate_first_derivative,
    )
    from analysis_8d.legacy.services.hessian_service import calculate_hessian

    data = _load_background(ro_conn, LEGACY_SAMPLE_BACKGROUND)
    candidates = data["candidates"]
    elements, e_den = to_scaled_int_matrix(data["solutions"])
    deltas, d_den = to_scaled_int_matrix([c["delta"] for c in candidates])
    characters = classify_characters(deltas, d_den, elements, e_den)
    fd = first_derivatives(characters, elements)

    critical = [k for k, c in enumerate(candidates) if c["is_critical_point"]]
    non_critical = [k for k, c in enumerate(candidates) if not c["is_critical_point"]]
    for k in critical[:1] + non_critical[:2]:
        legacy = calculate_first_derivative(candidates[k]["id"])
        assert [Fraction(int(v), e_den) for v in fd[k]] == [
            Fraction(str(x)) for x in legacy
        ]

    a9 = [Fraction(x) for x in data["a9"]]
    for k in critical[:1]:
        c = candidates[k]
        legacy = calculate_hessian(
            JoinedModuli8d(id=c["id"], a9=data["a9"], g9="", delta=c["delta"])
        )
        h = hessian(
            characters[k], elements, e_den, [Fraction(x) for x in c["delta"][2:]], a9
        )
        expected = np.array(
            [[float(Fraction(str(x))) for x in r] for r in legacy.tolist()]
        )
        assert np.array_equal(h, expected)
