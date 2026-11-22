"""
Exact integer (NumPy int64) versions of the 8D coset / cosmological constant /
first derivative / Hessian calculations.

Rational vectors are stored as (int64 array, common denominator) pairs, so no
floating point arithmetic is used until the Hessian is handed to eigvalsh.
All functions are pure (no DB access).
"""

from fractions import Fraction
from math import lcm
from typing import Sequence, Tuple, Union

import numpy as np

# Keep every intermediate value far below 2**63 (int64) and 2**53 (exact float64).
_INT64_SAFE = 2**62
_FLOAT_EXACT = 2**53


def to_scaled_int_matrix(
    rows: Sequence[Sequence[Union[str, int, Fraction]]],
) -> Tuple[np.ndarray, int]:
    """
    Convert rational vectors to an int64 matrix with a common denominator.

    Args:
        rows: rational vectors such as [["1/2", "0", ...], ...]. Strings must be
            integers or "p/q".
    Returns:
        (matrix, den): rows[i][j] == matrix[i, j] / den exactly.
    """
    pairs: list[list[Tuple[int, int]]] = []
    den = 1
    for row in rows:
        row_pairs = [_to_pair(x) for x in row]
        den = lcm(den, *(q for _, q in row_pairs))
        pairs.append(row_pairs)
    try:
        matrix = np.array(
            [[p * (den // q) for p, q in row_pairs] for row_pairs in pairs],
            dtype=np.int64,
        )
    except OverflowError:
        raise OverflowError("Scaled rational vectors do not fit in int64.") from None
    if matrix.size and (matrix.max() >= _INT64_SAFE or matrix.min() <= -_INT64_SAFE):
        raise OverflowError("Scaled rational vectors do not fit in int64.")
    return matrix, den


def _to_pair(x: Union[str, int, Fraction]) -> Tuple[int, int]:
    """(numerator, positive denominator) of a rational; faster than Fraction(str)."""
    if isinstance(x, str):
        p, _, q = x.partition("/")
        if not q:
            return int(p), 1
        num, den = int(p), int(q)
        if den <= 0:
            raise ValueError(f"Invalid rational string: {x!r}")
        return num, den
    f = Fraction(x)
    return f.numerator, f.denominator


def classify_characters(
    deltas: np.ndarray, delta_den: int, elements: np.ndarray, element_den: int
) -> np.ndarray:
    """
    Characters (4 delta . e) mod 4 for every pair of Wilson line and lattice element.

    Args:
        deltas: (K, 18) int64, Wilson lines multiplied by delta_den.
        elements: (S, 18) int64, massless solutions multiplied by element_den.
    Returns:
        (K, S) int8 array with values in {0, 1, 2, 3}.
    """
    if deltas.size == 0 or elements.size == 0:
        return np.zeros((deltas.shape[0], elements.shape[0]), dtype=np.int8)
    bound = (
        4 * deltas.shape[1] * int(np.abs(deltas).max()) * int(np.abs(elements).max())
    )
    if bound >= _INT64_SAFE:
        raise OverflowError("Inner products may overflow int64.")
    numerator = deltas @ elements.T
    numerator *= 4
    den = delta_den * element_den
    if np.any(numerator % den != 0):
        raise ValueError("4 delta . e is not an integer for some lattice elements.")
    numerator //= den
    numerator &= 3
    return numerator.astype(np.int8)


def cosmological_constants(characters: np.ndarray) -> np.ndarray:
    """24 + (number of character 0 states) - (number of character 2 states)."""
    return 24 + (characters == 0).sum(axis=1) - (characters == 2).sum(axis=1)


def first_derivatives(characters: np.ndarray, elements: np.ndarray) -> np.ndarray:
    """
    Sum of character 1 elements minus sum of character 3 elements.

    Returns:
        (K, 18) int64, multiplied by the denominator of `elements`.
    """
    weights = (characters == 1).astype(np.int64) - (characters == 3).astype(np.int64)
    return weights @ elements


def hessian(
    characters: np.ndarray,
    elements: np.ndarray,
    element_den: int,
    a8: Sequence[Fraction],
    a9: Sequence[Fraction],
) -> np.ndarray:
    """
    Hessian at one Wilson line, identical to get_hessian_components(0) - (2).

    Each state contributes u u^T with u = (w, w a8 / 2, w a9 / 2 + pi), with sign
    +1 for character 0 and -1 for character 2.

    Args:
        characters: (S,) characters of the massless solutions for this Wilson line.
        elements: (S, 18) int64 massless solutions (w, n, pi) times element_den.
        a8, a9: 16 rational components each.
    Returns:
        (33, 33) float64 matrix; each entry is the correctly rounded exact value.
    """
    a8_int, a8_den = to_scaled_int_matrix([a8])
    a9_int, a9_den = to_scaled_int_matrix([a9])
    scale = lcm(element_den, 2 * a8_den, 2 * a9_den)
    signs = (characters == 0).astype(np.int64) - (characters == 2).astype(np.int64)
    mask = signs != 0
    states = elements[mask]
    w = (states[:, 0] // element_den)[:, None]
    u = np.hstack(
        [
            w * scale,
            w * a8_int * (scale // (2 * a8_den)),
            w * a9_int * (scale // (2 * a9_den))
            + states[:, 2:] * (scale // element_den),
        ]
    )
    max_u = int(np.abs(u).max()) if u.size else 0
    if u.shape[0] * max_u * max_u >= _FLOAT_EXACT or scale * scale >= _FLOAT_EXACT:
        raise OverflowError("Hessian entries cannot be represented exactly.")
    h_int = u.T @ (signs[mask][:, None] * u)
    return h_int.astype(np.float64) / float(scale * scale)
