"""
Compare the integer/NumPy prototype with the current SymPy implementation.

1. Correctness: for every moduli_8d row of the selected moduli_9d rows, the
   cosmological constant, is_critical_point, Hessian eigenvalues and type computed
   by the prototype are compared with the values stored in the DB. Characters are
   compared with coset_8d for a sample of rows.
2. Speed: per-candidate time of the current SymPy functions and of the prototype
   (single process, same candidates).

The DB is opened read-only. Usage (from the repository root):
    python analysis/tests/benchmark_integer_vs_sympy.py [moduli_9d_id ...]
"""

import json
import random
import sqlite3
import sys
import time
from fractions import Fraction
from pathlib import Path

_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ANALYSIS_ROOT))

import numpy as np

from analysis_8d.legacy.services.coset_service import classify_lattice_elements
from analysis_8d.legacy.services.critical_point_service import (
    calculate_first_derivative,
)
from analysis_8d.legacy.services.hessian_service import calculate_hessian
from analysis_8d.services.integer_lattice_service import (
    classify_characters,
    cosmological_constants,
    first_derivatives,
    hessian,
    to_scaled_int_matrix,
)
from common.matrix_handler import SMH
from config.env_settings import ENV
from sqlite.entities import JoinedModuli8d, MasslessSolution9d

ROUND_DIGITS = ENV.analysis_8d_hessian_eigenvalue_round_digits
SYMPY_SAMPLE = 10
SYMPY_HESSIAN_SAMPLE = 2
CHARACTER_SAMPLE = 100

conn = sqlite3.connect(f"file:{ENV.database_path}?mode=ro", uri=True)


def eigen_summary(h) -> tuple:
    eigenvalues, cp_type = SMH.classify_critical_point_numerical(h)
    rounded = []
    for v in eigenvalues:
        r = round(float(v), ROUND_DIGITS)
        rounded.append(0.0 if r == 0.0 else r)
    return json.dumps([str(v) for v in rounded]), str(cp_type)


def run_prototype(sols, cands, a9):
    """Return results and timings of the integer/NumPy prototype for one background."""
    t0 = time.perf_counter()
    elements, e_den = to_scaled_int_matrix([s[1] for s in sols])
    t1 = time.perf_counter()
    deltas, d_den = to_scaled_int_matrix([c["delta"] for c in cands])
    t2 = time.perf_counter()
    chars = classify_characters(deltas, d_den, elements, e_den)
    cc = cosmological_constants(chars)
    crit = ~first_derivatives(chars, elements).any(axis=1)
    t3 = time.perf_counter()
    hess = {}
    for k in np.flatnonzero(crit):
        a8 = [Fraction(x) for x in cands[k]["delta"][2:]]
        hess[k] = eigen_summary(hessian(chars[k], elements, e_den, a8, a9))
    t4 = time.perf_counter()
    times = dict(
        solutions=t1 - t0, deltas=t2 - t1, coset_cc_crit=t3 - t2, hessian=t4 - t3
    )
    return chars, cc, crit, hess, times


def check_characters(m9_id, sols, cands, chars, rng):
    sol_index = {s[0]: j for j, s in enumerate(sols)}
    mismatches = 0
    for k in rng.sample(range(len(cands)), min(CHARACTER_SAMPLE, len(cands))):
        rows = conn.execute(
            "SELECT massless_solution_9d_id, character FROM coset_8d WHERE moduli_8d_id = ?",
            (cands[k]["id"],),
        ).fetchall()
        if len(rows) != len(sols) or any(chars[k, sol_index[s]] != c for s, c in rows):
            mismatches += 1
    return mismatches


def time_sympy(m9_id, sols, cands, crit, a9_raw, rng):
    ms_list = [
        MasslessSolution9d(id=s[0], moduli_9d_id=m9_id, element=s[1]) for s in sols
    ]
    sample = rng.sample(range(len(cands)), min(SYMPY_SAMPLE, len(cands)))
    t0 = time.perf_counter()
    for k in sample:
        delta = SMH.create_vector_from_str_list(cands[k]["delta"])
        classify_lattice_elements(delta, cands[k]["id"], ms_list)
    t1 = time.perf_counter()
    for k in sample:
        calculate_first_derivative(cands[k]["id"])
    t2 = time.perf_counter()
    crit_idx = list(np.flatnonzero(crit))[:SYMPY_HESSIAN_SAMPLE]
    for k in crit_idx:
        moduli = JoinedModuli8d(
            id=cands[k]["id"], a9=a9_raw, g9="", delta=cands[k]["delta"]
        )
        eigen_summary(calculate_hessian(moduli=moduli))
    t3 = time.perf_counter()
    n = len(sample)
    return dict(
        coset=(t1 - t0) / n,
        first_derivative=(t2 - t1) / n,
        hessian=(t3 - t2) / len(crit_idx) if crit_idx else float("nan"),
    )


def main():
    rng = random.Random(0)
    all_ids = [
        r[0]
        for r in conn.execute("SELECT DISTINCT moduli_9d_id FROM moduli_8d ORDER BY 1")
    ]
    target_ids = [int(x) for x in sys.argv[1:]] or all_ids
    sympy_ids = set(int(x) for x in sys.argv[1:]) or {1, 25, 34}
    totals = dict(cands=0, cc_ng=0, crit_ng=0, hess_ng=0, hess_n=0, char_ng=0, char_n=0)
    print(
        "moduli_9d   M    S | NumPy ms/cand (coset+cc+crit) | NumPy ms/hessian | SymPy ms/cand coset, 1st | SymPy ms/hessian"
    )
    for m9_id in target_ids:
        sols = [
            (r[0], json.loads(r[1]))
            for r in conn.execute(
                "SELECT id, element FROM massless_solution_9d WHERE moduli_9d_id = ? ORDER BY id",
                (m9_id,),
            )
        ]
        if not sols:
            continue
        cands = [
            dict(
                id=r[0],
                delta=json.loads(r[1]),
                cc=r[2],
                crit=r[3],
                hessian=r[4],
                type=r[5],
            )
            for r in conn.execute(
                "SELECT id, delta, cosmological_constant, is_critical_point, hessian, type "
                "FROM moduli_8d WHERE moduli_9d_id = ? ORDER BY id",
                (m9_id,),
            )
        ]
        a9_raw = json.loads(
            conn.execute("SELECT a9 FROM moduli_9d WHERE id = ?", (m9_id,)).fetchone()[
                0
            ]
        )
        a9 = [Fraction(x) for x in a9_raw]

        chars, cc, crit, hess, t = run_prototype(sols, cands, a9)

        totals["cands"] += len(cands)
        totals["cc_ng"] += sum(int(cc[k]) != c["cc"] for k, c in enumerate(cands))
        totals["crit_ng"] += sum(
            bool(crit[k]) != bool(c["crit"]) for k, c in enumerate(cands)
        )
        for k, (h, cp_type) in hess.items():
            totals["hess_n"] += 1
            totals["hess_ng"] += (h, cp_type) != (cands[k]["hessian"], cands[k]["type"])
        totals["char_n"] += min(CHARACTER_SAMPLE, len(cands))
        totals["char_ng"] += check_characters(m9_id, sols, cands, chars, rng)

        line = "%9d %6d %4d | %29.4f | %16.3f |" % (
            m9_id,
            len(cands),
            len(sols),
            (t["deltas"] + t["coset_cc_crit"]) / len(cands) * 1e3,
            t["hessian"] / max(len(hess), 1) * 1e3,
        )
        if m9_id in sympy_ids:
            s = time_sympy(m9_id, sols, cands, crit, a9_raw, rng)
            line += " %10.1f, %10.1f | %16.1f" % (
                s["coset"] * 1e3,
                s["first_derivative"] * 1e3,
                s["hessian"] * 1e3,
            )
        print(line, flush=True)

    print()
    print("candidates checked:", totals["cands"])
    print("cosmological constant mismatches:", totals["cc_ng"])
    print("is_critical_point mismatches:", totals["crit_ng"])
    print(
        "Hessian (eigenvalues, type) mismatches: %d / %d"
        % (totals["hess_ng"], totals["hess_n"])
    )
    print(
        "character mismatches vs coset_8d: %d / %d sampled candidates"
        % (totals["char_ng"], totals["char_n"])
    )


if __name__ == "__main__":
    main()
