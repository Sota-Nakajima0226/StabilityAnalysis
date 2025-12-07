import numpy as np
from pathlib import Path
from typing import List
from sympy import Rational, Matrix

from common.json_handler import JsonHandler
from common.weight import FUND_WEIGHTS_SP_10D, FUND_WEIGHTS_NP
from common.file_path import INPUT_DIR_PATH
from model.moduli import Moduli9DInput
from model.lie_algebra import SemiSimpleLieAlg

jh: JsonHandler = JsonHandler()
MAX_ENHANCING_MODULI_9D_PATH: Path = INPUT_DIR_PATH / "9d" / "max_enhancing_moduli.json"

MAX_ENHANCING_MODULI_9D_JSON = jh.load_json(MAX_ENHANCING_MODULI_9D_PATH)


def get_moduli_np_9d_from_dict() -> List[dict]:
    """
    Get moduli info from JSON.

    Args:
      index (dict): index of moduli list

    Returns:
      dict: moduli information as the following form:
        {
          "labels": label of removed nodes (List[str]),
          "A1": {
            "k": Kac mark (int)
            "vector": fundamental weight of the 1st removed node (np.ndarray),
          },
          "A2": {
            "k": Kac mark (int)
            "vector": fundamental weight of the 2nd removed node (np.ndarray),
          },
          "G": {
            "num": numerator (int),
            "den": denominator (int)
          },
          "L": enhanced AED gauge groups (dict)
        }
    """
    result = []
    for mem in MAX_ENHANCING_MODULI_9D_JSON:
        removed_node_labels = mem["removed_nodes"]
        result.append(
            {
                "labels": removed_node_labels,
                "A1": FUND_WEIGHTS_NP[removed_node_labels[0]],
                "A2": FUND_WEIGHTS_NP[removed_node_labels[1]],
                "G": mem["G"],
                "L": mem["L"],
            }
        )
    return result


MAX_ENHANCING_MODULI_NP_9D = get_moduli_np_9d_from_dict()


def get_moduli_sp_9d_from_dict() -> List[Moduli9DInput]:
    """
    Get moduli info from JSON for sympy.

    Args:
      index (dict): index of moduli list

    Returns:
      List[Moduli9D]: list of the moduli in 9D.
    """
    result = []
    for mem in MAX_ENHANCING_MODULI_9D_JSON:
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
                g9=Rational(mem["G"]["num"], mem["G"]["den"]),
                lie_algebra=SemiSimpleLieAlg(**mem["L"]),
            )
        )
    return result


MAX_ENHANCING_MODULI_SP_9D = get_moduli_sp_9d_from_dict()
