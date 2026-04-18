from typing import List

import numpy as np
from sympy import Matrix, Rational
from itertools import combinations, product
from common.matrix_handler import SMH


def generate_e8_root_np_vectors() -> List[np.ndarray]:
    """
    Generate 240 non-zero root vectors of E_8 by numpy.

    Returns:
      List[np.ndarray]: a set of non-zero roots of E_8
    """
    root_vectors = []
    # Generate integer roots: (±1, ±1, 0, 0, 0, 0, 0, 0)
    indices = combinations(range(8), 2)
    for idx in indices:
        for signs in product([1, -1], repeat=2):
            vec = np.zeros(8)
            vec[idx[0]], vec[idx[1]] = signs
            root_vectors.append(vec)
    # Generate half-integer roots: (±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2)
    signs = [-1 / 2, 1 / 2]
    for bits in range(256):
        vec = np.array(
            [(bits >> i & 1) * signs[1] + (~bits >> i & 1) * signs[0] for i in range(8)]
        )
        if np.sum(vec) % 2 == 0:
            root_vectors.append(vec)
    return root_vectors


E8_ROOTS_NP: List[np.ndarray] = generate_e8_root_np_vectors()


def generate_e8_root_sp_vectors() -> List[Matrix]:
    """
    Generate 240 non-zero root vectors of E_8 by sympy.

    Returns:
      List[Matrix]: a set of non-zero roots of E_8
    """
    root_vectors = []
    # Generate integer roots: (±1, ±1, 0, 0, 0, 0, 0, 0)
    indices = combinations(range(8), 2)
    for idx in indices:
        for signs in product([1, -1], repeat=2):
            vec = SMH.create_constant_vector(0)
            vec[idx[0]], vec[idx[1]] = signs
            root_vectors.append(vec)
    # Generate half-integer roots: (±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2)
    signs = [Rational(1, 2), Rational(-1, 2)]
    for bits in range(256):
        element = [
            (bits >> i & 1) * signs[1] + (~bits >> i & 1) * signs[0] for i in range(8)
        ]
        if sum(element) % 2 == 0:
            root_vectors.append(Matrix(element))
    return root_vectors


E8_ROOTS_SP: List[Matrix] = generate_e8_root_sp_vectors()
