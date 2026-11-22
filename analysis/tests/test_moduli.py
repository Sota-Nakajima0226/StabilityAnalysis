import os
import sys
import types
import unittest
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from sympy import Matrix, Rational

sys.path.append(str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_PATH", "nonsusy_strings.db")
dotenv_stub = types.ModuleType("dotenv")
setattr(dotenv_stub, "load_dotenv", cast(Any, lambda *args, **kwargs: None))
sys.modules.setdefault("dotenv", dotenv_stub)

from common import moduli
from model.lie_algebra import SemiSimpleLieAlg
from model.weight import FundWeightSp


class TestGetModuli9DMaxEnhancingFromDict(unittest.TestCase):
    @patch("common.moduli.jh.load_json")
    def test_builds_moduli9d_input_from_json(self, mock_load_json):
        mock_load_json.return_value = [
            {
                "removed_nodes": ["0", "10"],
                "G": {"num": 1, "den": 2},
                "L": {"A": [1], "D": [2], "E": []},
            }
        ]

        fake_weights = {
            "0": FundWeightSp(vector=Matrix([[2], [4]]), k=2),
            "10": FundWeightSp(vector=Matrix([[3], [9]]), k=3),
        }

        with patch("common.moduli.FUND_WEIGHTS_SP_10D", fake_weights):
            result = moduli.get_moduli_9d_max_enhancing_from_dict()

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry.removed_nodes, ["0", "10"])
        self.assertEqual(entry.a9_1, Matrix([[1], [2]]))
        self.assertEqual(entry.a9_2, Matrix([[1], [3]]))
        self.assertEqual(entry.g9, Rational(1, 2))
        self.assertEqual(entry.lie_algebra, SemiSimpleLieAlg(A=[1], D=[2], E=[]))
        mock_load_json.assert_called_once_with(moduli.MAX_ENHANCING_MODULI_9D_PATH)


if __name__ == "__main__":
    unittest.main()
