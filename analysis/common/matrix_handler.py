import sympy as sp
import numpy as np
from enum import Enum, auto
from typing import Any, List, Union, Tuple, Dict, cast
from sympy import Matrix, Rational, sympify


class CriticalPointType(Enum):
    POSITIVE = "POSITIVE"
    SEMIPOSITIVE = "SEMIPOSITIVE"
    NEGATIVE = "NEGATIVE"
    SEMINEGATIVE = "SEMINEGATIVE"
    SADDLE_POINT = "SADDLE_POINT"
    ZERO = "ZERO"


class SpMatrixHandler:
    """
    Class to handle matrices by sympy.
    """

    @staticmethod
    def create_vector(components: List[Union[int, Rational]], den: int = 1) -> Matrix:
        """
        Create a vector from a list of integers and a denominator.
        Args:
          components (List[Any]): components of a vector.
          den (int): overall denominator.
        Returns:
          Matrix: vector with rational elements.
        """
        if den == 0:
            raise ValueError("Denominator must not be zero.")
        return Matrix(components) / den

    @staticmethod
    def create_constant_vector(
        number: Union[int, Rational], dimension: int = 8
    ) -> Matrix:
        """
        Create a vector of which all elements are the same value.
        Args:
          num (int): numerator of elements.
          den (int): denominator of elements.
          dimension (int): dimension of the vector.
        Returns:
          Matrix: vector of which all elements are the same value.
        """
        elements = [number] * dimension
        return Matrix(elements)

    @staticmethod
    def linear_combination(
        vectors: List[Matrix], coefficients: List[Rational]
    ) -> Matrix:
        """
        Take linear combination of vectors with coefficients.
        Args:
          vectors (List[Matrix]): list of vectors.
          coefficients (List[Rational]): list of coefficients.
        Returns:
          Matrix: linear combined vector.
        """
        if len(vectors) != len(coefficients):
            raise ValueError("The number of vectors and coefficients must be the same.")
        result = Matrix.zeros(*vectors[0].shape)
        for vec, coef in zip(vectors, coefficients):
            result += coef * vec
        return result

    @staticmethod
    def dot_product(v1: Matrix, v2: Matrix) -> Rational:
        """
        Calculate the inner product of two vectors.
        Args:
          v1 (Matrix): vector1.
          v2 (Matrix): vector2.
        Returns:
          Rational: inner product of v1 and v2.
        """
        if v1.shape != v2.shape:
            raise ValueError("The dimensions of two vectors must be the same.")
        return v1.dot(v2)

    @staticmethod
    def concat_vectors(vectors: List[Matrix]) -> Matrix:
        """
        Concatenate multiple vectors.
        Args:
          vectors (List[Matrix]): list of vectors.
        Returns:
          Matrix: concatenated vector.
        """
        if not vectors:
            return Matrix([], 1)
        result = vectors[0]
        for v in vectors[1:]:
            result = result.col_join(v)
        return result

    @staticmethod
    def create_vector_from_str_list(str_list: List[str]) -> Matrix:
        """
        Create a vector from a list of number strings.
        Args:
          str_list (List[str]): list of number strings.
        Returns:
          Matrix: vector generated from str_list.
        """
        return Matrix([sympify(s) for s in str_list])

    @staticmethod
    def extend_vector(
        vector: Matrix, values: List[Union[int, Rational]], prepend: bool = True
    ) -> Matrix:
        """
        Extend a vector by adding values to the begging or end.
        Args:
          vector (Matrix): vector to be extended.
          values (List[str]): values to be added as vector elements.
          prepend (bool): prepend or append
        Returns:
          Matrix: extended vector.
        """
        return (
            Matrix.vstack(Matrix(values), vector)
            if prepend
            else Matrix.vstack(vector, Matrix(values))
        )

    @staticmethod
    def create_zero_matrix(dimension: int) -> Matrix:
        """
        Create a matrix with all components being zero.
        Args:
          dimension (int): dimension of the matrix.
        Returns:
          Matrix: matrix with all components being zero.
        """
        return sp.zeros(dimension, dimension)

    @staticmethod
    def classify_critical_point(
        hessian: Matrix, precision: int = 4
    ) -> Tuple[Dict[float, int], CriticalPointType]:
        """
        Determine the type of the critical point by calculating eigenvalues of the hessian.

        Args:
            hessian (Matrix): Hessian at the critical point.
            precision (int, default 4): precision.
        Returns:
            Dict[float, int]:
                key: eigenvalues
                value: multiplicity
            CriticalPointType: type of the critical point.
        """
        # Calculate eigenvalues
        raw_eigs = cast(Dict[Any, int], hessian.eigenvals())

        eigs = {}
        for val, mult in raw_eigs.items():
            rounded_val = round(float(val.evalf()), precision)
            if rounded_val == 0.0:  # Replace -0.0 to 0.0
                rounded_val = 0.0
            eigs[rounded_val] = eigs.get(rounded_val, 0) + mult

        has_pos = any(v > 0 for v in eigs.keys())
        has_neg = any(v < 0 for v in eigs.keys())
        has_zero = any(v == 0 for v in eigs.keys())

        if has_pos and has_neg:
            return eigs, CriticalPointType.SADDLE_POINT

        if has_pos:
            if has_zero:
                return eigs, CriticalPointType.SEMIPOSITIVE
            else:
                return eigs, CriticalPointType.POSITIVE

        if has_neg:
            if has_zero:
                return eigs, CriticalPointType.SEMINEGATIVE
            else:
                return eigs, CriticalPointType.NEGATIVE

        return eigs, CriticalPointType.ZERO

    @staticmethod
    def classify_critical_point_numerical(
        hessian: Matrix, epsilon: float = 1e-10
    ) -> Tuple[np.ndarray, CriticalPointType]:
        """
        Determine the type of the critical point by calculating eigenvalues of the hessian.

        Args:
            hessian (Matrix): Hessian at the critical point.
            epsilon (int, default 1e-10): threshold to be considered as 0.
        Returns:
            Dict[float, int]:
                key: eigenvalues
                value: multiplicity
            CriticalPointType: type of the critical point.
        """
        # Convert a sympy matrix to a numpy matrix
        h_np = np.array(hessian.tolist(), dtype=float)

        # Calculate eigenvalues
        eigs = np.linalg.eigvalsh(h_np)

        has_pos = np.any(eigs > epsilon)
        has_neg = np.any(eigs < -epsilon)
        has_zero = np.any(np.abs(eigs) <= epsilon)

        if has_pos and has_neg:
            return eigs, CriticalPointType.SADDLE_POINT

        if has_pos:
            if has_zero:
                return eigs, CriticalPointType.SEMIPOSITIVE
            else:
                return eigs, CriticalPointType.POSITIVE

        if has_neg:
            if has_zero:
                return eigs, CriticalPointType.SEMINEGATIVE
            else:
                return eigs, CriticalPointType.NEGATIVE

        return eigs, CriticalPointType.ZERO


SMH = SpMatrixHandler()
