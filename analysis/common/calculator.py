from typing import List

import math
from itertools import combinations
from common.constants import PRECISION


class Calculator:
    """
    Class to perform common calculations.
    """

    def __init__(self, precision: int = 10):
        self.precision = precision

    def round(self, number: float) -> float:
        """
        Round a number by the precision.

        Args:
            number (float): a number to be rounded.
        Returns:
            float: a number rounded.
        """
        return round(number, self.precision)

    def is_equal_float_num(
        self, lhs: float, rhs: float, ambiguity: int = 1, floor: bool = False
    ) -> bool:
        """
        Check if two float number are equal or not.

        Args:
            lhs (float): a float number of the left hand side.
            rhs (float): a float number of the right hand side.
            ambiguity (int): ambiguity in comparison. rhs and lhs are compared with precision minus ambiguity.
        Returns:
            bool:
                True: lhs = rhs
                False: lhs != rhs
        """
        precision = self.precision - ambiguity
        if floor:
            scale = 10**precision
            return math.floor(lhs * scale) == math.floor(rhs * scale)
        else:
            return round(lhs, precision) == round(rhs, precision)

    def compare_float_num(
        self, lhs: float, rhs: float, ambiguity: int = 1, floor: bool = False
    ) -> bool:
        """
        Compare two float values.

        Args:
            lhs (float): a float number of the left hand side.
            rhs (float): a float number of the right hand side.
            ambiguity (int): ambiguity in comparison. rhs and lhs are compared with precision minus ambiguity.
        Returns:
            bool:
                True: lhs > rhs.
                False: lhs <= rhs.
        """
        precision = self.precision - ambiguity
        if floor:
            scale = 10**precision
            return math.floor(lhs * scale) > math.floor(rhs * scale)
        else:
            return round(lhs, precision) > round(rhs, precision)

    def is_integer(self, value: float, ambiguity: int = 1) -> bool:
        """
        Check if a number is an integer or not.

        Args:
            value (float): a number.
            ambiguity (int): ambiguity in comparison. value is checked if it is an integer with precision minus ambiguity.
        Returns:
            bool:
                True: value is an integer.
                False: value is not an integer.
        """
        rounded_value = round(value, (self.precision - ambiguity))
        return rounded_value.is_integer()

    def calculate_cos(self, arg: float) -> float:
        """
        Calculate a cosine of an argument.

        Args:
            arg (float): an argument of cosine.
        Returns:
            float: cos(pi * arg)
        """
        phase = math.pi * arg
        cos = math.cos(phase)
        return round(cos, self.precision)

    def calculate_sin(self, arg: float) -> float:
        """
        Calculate a sine of an argument.

        Args:
            arg (float): an argument of sine.
        Returns:
            float: sin(pi * arg)
        """
        phase = math.pi * arg
        sin = math.sin(phase)
        return round(sin, self.precision)

    def check_pairwise_coprime(numbers: List[int]) -> bool:
        for a, b in combinations(numbers, 2):
            if a == 0 or b == 0:
                continue
            if math.gcd(a, b) != 1:
                return False
            return True

    def count_nonzero_roots(self, algebra: dict) -> int:
        """
        Count the number of non-zero roots of ADE algebra.

        Args:
          algebra (dict): dictionary specifying a ADE algebra. e.g. for A_1 + A_2 + D_2 + E_6,
            {
              "A": [1, 2]
              "D": [2]
              "E": [6]
            }
        Return:
          int: the number of nonzero roots of the ADE algebra
        """
        A_list = algebra["A"] if "A" in algebra else []
        D_list = algebra["D"] if "D" in algebra else []
        E_list = algebra["E"] if "E" in algebra else []
        num = 0
        if len(A_list) != 0:
            for n in A_list:
                num += n * (n + 1)
        if len(D_list) != 0:
            for n in D_list:
                num += 2 * n * (n - 1)
        if len(E_list) != 0:
            for n in E_list:
                if n == 6:
                    num += 72
                elif n == 7:
                    num += 126
                elif n == 8:
                    num += 240
        return num


CALCULATOR: Calculator = Calculator(precision=PRECISION)
