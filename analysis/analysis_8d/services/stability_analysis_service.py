"""
Cosmological constant, critical point and Hessian of 8D moduli for one 9D background,
computed with the exact integer functions of integer_lattice_service.

No DB access: the job reads the inputs and writes the returned rows.
"""

import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Sequence, Tuple

import numpy as np

from analysis_8d.services.integer_lattice_service import (
    classify_characters,
    cosmological_constants,
    first_derivatives,
    hessian,
    to_scaled_int_matrix,
)
from common.matrix_handler import SMH


@dataclass(frozen=True)
class BackgroundLattice:
    """Massless solutions and a9 of one moduli_9d row in integer form."""

    moduli_9d_id: int
    elements: np.ndarray
    element_den: int
    a9: Tuple[Fraction, ...]


def prepare_background(
    moduli_9d_id: int,
    massless_solutions: Sequence[Sequence[str]],
    a9: Sequence[str],
) -> BackgroundLattice:
    """
    Convert the massless solutions (w, n, pi) and a9 of one background.

    Args:
        moduli_9d_id: id of the background.
        massless_solutions: elements of massless_solution_9d, e.g. [["1", "0", "1/2", ...]].
        a9: a9 of moduli_9d.
    """
    elements, element_den = to_scaled_int_matrix(massless_solutions)
    return BackgroundLattice(
        moduli_9d_id=moduli_9d_id,
        elements=elements,
        element_den=element_den,
        a9=tuple(Fraction(x) for x in a9),
    )


def format_eigenvalues(eigenvalues: np.ndarray, round_digits: int) -> str:
    """Same format as the legacy Hessian job: JSON list of rounded value strings."""
    rounded = []
    for v in eigenvalues:
        r = round(float(v), round_digits)
        rounded.append(0.0 if r == 0.0 else r)
    return json.dumps([str(v) for v in rounded])


def analyze_candidates(
    background: BackgroundLattice,
    moduli_8d_ids: Sequence[int],
    deltas: Sequence[Sequence[str]],
    round_digits: int,
) -> list[dict[str, Any]]:
    """
    Analyze moduli_8d candidates of one background.

    Args:
        background: result of prepare_background.
        moduli_8d_ids: ids of the candidates.
        deltas: Wilson lines of the candidates (18 rational strings each).
        round_digits: decimals of the saved Hessian eigenvalues.
    Returns:
        Rows for bulk_update_by_id on moduli_8d. hessian and type are None for
        candidates that are not critical points.
    """
    if not moduli_8d_ids:
        return []
    delta_matrix, delta_den = to_scaled_int_matrix(deltas)
    characters = classify_characters(
        delta_matrix, delta_den, background.elements, background.element_den
    )
    cosmological_constant = cosmological_constants(characters)
    is_critical = np.all(
        first_derivatives(characters, background.elements) == 0, axis=1
    )

    rows: list[dict[str, Any]] = []
    for k, moduli_8d_id in enumerate(moduli_8d_ids):
        row: dict[str, Any] = {
            "id": int(moduli_8d_id),
            "cosmological_constant": int(cosmological_constant[k]),
            "is_critical_point": int(is_critical[k]),
            "hessian": None,
            "type": None,
        }
        if is_critical[k]:
            a8 = [Fraction(x) for x in deltas[k][2:]]
            h = hessian(
                characters[k],
                background.elements,
                background.element_den,
                a8,
                background.a9,
            )
            eigenvalues, cp_type = SMH.classify_critical_point_numerical(h)
            row["hessian"] = format_eigenvalues(eigenvalues, round_digits)
            row["type"] = str(cp_type)
        rows.append(row)
    return rows
