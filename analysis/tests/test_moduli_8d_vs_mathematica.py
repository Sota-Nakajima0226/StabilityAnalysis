"""
Validate Python moduli_8d results against Mathematica reference CSV exports.
"""

from __future__ import annotations

import pytest

from compare_moduli_8d import (
    MIN_MATCH_RATIO,
    MIN_MATCHED_ROWS,
    compare_cosmological_constants,
    compare_critical_points,
    compare_hessians,
    compute_coverage,
    format_mismatches,
)


def test_minimum_coverage(comparison_context, cosmo_csv):
    ctx = comparison_context
    matched, csv_count, db_count = compute_coverage(
        ctx["db_index"],
        cosmo_csv,
        ctx["mma_m9_map"],
        ctx["active_mma_m9_ids"],
    )
    assert matched >= MIN_MATCHED_ROWS, (
        f"Too few matched rows: matched={matched}, "
        f"csv_in_scope={csv_count}, db_in_scope={db_count}, "
        f"active_mma_m9_ids={sorted(ctx['active_mma_m9_ids'], key=int)}"
    )
    if csv_count > 0 and MIN_MATCH_RATIO > 0:
        ratio = matched / csv_count
        assert ratio >= MIN_MATCH_RATIO, (
            f"Match ratio {ratio:.4f} below REFERENCE_MIN_MATCH_RATIO={MIN_MATCH_RATIO}"
        )


def test_cosmological_constant_matches_reference(comparison_context, cosmo_csv):
    ctx = comparison_context
    stats = compare_cosmological_constants(
        ctx["db_index"],
        cosmo_csv,
        ctx["mma_m9_map"],
        ctx["active_mma_m9_ids"],
    )
    assert stats.matched >= MIN_MATCHED_ROWS
    assert not stats.mismatches, (
        f"{len(stats.mismatches)} cosmological_constant mismatch(es) "
        f"(matched={stats.matched}, csv_only={stats.csv_only})\n"
        f"{format_mismatches(stats)}"
    )


def test_critical_point_flag_matches_reference(
    comparison_context, critical_point_csv
):
    ctx = comparison_context
    stats = compare_critical_points(
        ctx["db_index"],
        critical_point_csv,
        ctx["mma_m9_map"],
        ctx["active_mma_m9_ids"],
    )
    assert stats.matched >= MIN_MATCHED_ROWS
    assert not stats.mismatches, (
        f"{len(stats.mismatches)} is_critical_point mismatch(es) "
        f"(matched={stats.matched}, csv_only={stats.csv_only})\n"
        f"{format_mismatches(stats)}"
    )


def test_hessian_eigenvalues_and_type_match_reference(
    comparison_context, hessian_csv, eigenvalue_round_digits
):
    ctx = comparison_context
    stats = compare_hessians(
        ctx["db_index"],
        hessian_csv,
        ctx["mma_m9_map"],
        ctx["active_mma_m9_ids"],
        eigenvalue_round_digits=eigenvalue_round_digits,
    )
    assert stats.matched >= 1, (
        "No hessian CSV rows matched DB (partial DB or hessian job not run?)"
    )
    assert not stats.mismatches, (
        f"{len(stats.mismatches)} hessian/type mismatch(es) "
        f"(matched={stats.matched}, csv_only={stats.csv_only})\n"
        f"{format_mismatches(stats)}"
    )
