from pathlib import Path
from typing import List, cast
from sympy import Rational, Matrix
from itertools import combinations_with_replacement

from config.yaml_settings import YAML
from common.json_handler import JsonHandler
from common.matrix_handler import SMH
from common.weight import FUND_WEIGHTS_SP_10D
from model.moduli import Moduli9DInput
from model.lie_algebra import SemiSimpleLieAlg

jh: JsonHandler = JsonHandler()
MAX_ENHANCING_MODULI_9D_PATH: Path = (
    YAML.paths.input_dir / "9d" / "max_enhancing_moduli.json"
)
COEFFICIENTS_JSON_PATH: Path = YAML.paths.input_dir / "9d" / "coefficients.json"


def get_moduli_9d_max_enhancing_from_dict() -> List[Moduli9DInput]:
    """
    Get moduli info from JSON for sympy.

    Args:
      index (dict): index of moduli list

    Returns:
      List[Moduli9D]: list of the moduli in 9D.
    """
    result = []
    max_enhancing_moduli_9d_json = jh.load_json(MAX_ENHANCING_MODULI_9D_PATH)
    for mem in max_enhancing_moduli_9d_json:
        removed_nodes = mem["removed_nodes"]
        fund_weight1 = FUND_WEIGHTS_SP_10D[removed_nodes[0]]
        fund_weight2 = FUND_WEIGHTS_SP_10D[removed_nodes[1]]
        a9_1: Matrix = fund_weight1.vector / fund_weight1.k
        a9_2: Matrix = fund_weight2.vector / fund_weight2.k
        result.append(
            Moduli9DInput(
                removed_nodes=removed_nodes,
                a9_1=a9_1,
                a9_2=a9_2,
                g9=cast(Rational, Rational(mem["G"]["num"], mem["G"]["den"])),
                lie_algebra=SemiSimpleLieAlg(**mem["L"]),
            )
        )
    return result


def generate_moduli_9d_from_coefficients() -> List[Moduli9DInput]:
    result = []
    coefficients_json = jh.load_json(COEFFICIENTS_JSON_PATH)
    for c1, c2 in combinations_with_replacement(coefficients_json, 2):
        removed_nodes = []
        nonzero_coefficients1 = []
        nonzero_coefficients2 = []
        fund_weights1 = []
        fund_weights2 = []
        node = 0
        for coefficient in c1["s"]:
            if coefficient != 0:
                removed_nodes.append(str(node))
                nonzero_coefficients1.append(coefficient)
                fund_weights1.append(FUND_WEIGHTS_SP_10D[str(node)].vector)
            node += 1
        node = 10
        for coefficient in c2["s"]:
            if coefficient != 0:
                removed_nodes.append(str(node))
                nonzero_coefficients2.append(coefficient)
                fund_weights2.append(FUND_WEIGHTS_SP_10D[str(node)].vector)
            node += 1
        a9_1: Matrix = (
            SMH.linear_combination(fund_weights1, nonzero_coefficients1) / c1["N"]
        )
        a9_2: Matrix = (
            SMH.linear_combination(fund_weights2, nonzero_coefficients2) / c2["N"]
        )
        lie_algebra = SemiSimpleLieAlg(
            A=c1["L"]["A"] + c2["L"]["A"],
            D=c1["L"]["D"] + c2["L"]["D"],
            E=c1["L"]["E"] + c2["L"]["E"],
        )
        result.append(
            Moduli9DInput(
                removed_nodes=removed_nodes,
                a9_1=a9_1,
                a9_2=a9_2,
                g9=cast(Rational, Rational(0)),
                lie_algebra=lie_algebra,
            )
        )
    return result
