from typing import Any, List, Union, cast
import numpy as np
from scipy.linalg import eigh

from sympy import Matrix, Rational, sympify
from common.constants import PRECISION
from common.calculator import CALCULATOR


class NpMatrixHandler:
    """
    Class to handle matrices by numpy.
    """

    def __init__(self, precision: int = 10):
        self.precision = precision

    def create_vector(
        self, components: List[Union[int, float]], round: bool = True
    ) -> np.ndarray:
        """
        Create a vector from a list of numbers.
        Args:
          components (List[int] or List[float]): components of a vector.
          den (int): overall denominator.
        Returns:
          Matrix: vector with rational elements.
        """
        if round:
            return np.round(np.array(components, dtype=np.float64), self.precision)
        else:
            return np.array(components, dtype=np.float64)

    def create_constant_vector(
        self, value: Union[int, float], dimension: int = 8
    ) -> np.ndarray:
        """
        Create a constant vector whose components are the same value.

        """
        return np.full(dimension, value, dtype=np.float64)

    def scalar_multiplication(
        self,
        vector: np.ndarray,
        number: Union[int, float],
        inverse: bool = False,
        round: bool = True,
    ) -> np.ndarray:
        if inverse:
            v = vector / number
        else:
            v = vector * number
        return np.round(v, self.precision) if round else v

    def concat_vectors(self, vectors: List[np.ndarray]) -> np.ndarray:
        """
        Concatenate multiple vectors.
        Args:
          vectors (List[Matrix]): list of vectors.
        Returns:
          Matrix: concatenated vector.
        """
        return np.concatenate(vectors, dtype=np.float64)

    def linear_combination(
        self,
        vectors: List[np.ndarray],
        coefficients: List[Union[int, float]],
        round: bool = True,
    ) -> np.ndarray:
        """
        Calculate a liner combination.
        Args:
            coeffs (List[float] or List[int]): a list of coefficients.
            vectors (List[np.array]): a list of vectors.
        Returns:
            np.array: the liner combined vector.
        """
        if len(vectors) != len(coefficients):
            raise ValueError("The number of vectors and coefficients must be the same.")
        result = sum(c * v for c, v in zip(coefficients, vectors))
        if round:
            return np.round(result, self.precision)
        else:
            return cast(np.ndarray, result)

    def dot_product(self, v1: np.ndarray, v2: np.ndarray, round: bool = True) -> float:
        """
        Calculate the inner product of two vectors.
        Args:
            v1 (np.ndarray): vector1.
            v2 (np.ndarray): vector2.
        Returns:
            float: inner product of v1 and v2.
        """
        if round:
            return CALCULATOR.round(np.dot(v1, v2))
        else:
            return np.dot(v1, v2)

    def get_eigenvalues(self, matrix: np.ndarray, round: bool = True) -> Any:
        """
        Solve a standard or generalized eigenvalue problem for a complex Hermitian or real symmetric matrix.

        Args:
          matrix (np.ndarray): A complex Hermitian or real symmetric matrix whose eigenvalues and eigenvectors will be computed.
        Returns:
          ndarray: The eigenvalues of matrix.
        """
        eigen_values = eigh(matrix, eigvals_only=True)
        return np.round(eigen_values, self.precision) if round else eigen_values

    def classify_critical_points(self, eigenvalues: np.ndarray) -> str:
        if np.all(eigenvalues > 0):
            return "minimum"
        elif np.all(eigenvalues < 0):
            return "maximum"
        elif np.any(eigenvalues > 0) and np.any(eigenvalues < 0):
            return "saddle_point"
        elif np.any(eigenvalues >= 0) or np.any(eigenvalues <= 0):
            return "undeterminable"
        else:
            return "saddle_point"


NMH = NpMatrixHandler(precision=PRECISION)


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


SMH = SpMatrixHandler()
