from pathlib import Path
from typing import List, cast
from sympy import Rational, Matrix

from config.yaml_settings import YAML
from common.json_handler import JsonHandler
from common.weight import FUND_WEIGHTS_SP_10D
from model.moduli import Moduli9DInput
from model.lie_algebra import SemiSimpleLieAlg

jh: JsonHandler = JsonHandler()
MAX_ENHANCING_MODULI_9D_PATH: Path = (
    YAML.paths.input_dir / "9d" / "max_enhancing_moduli.json"
)


def get_moduli_sp_9d_from_dict() -> List[Moduli9DInput]:
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


MAX_ENHANCING_MODULI_SP_9D = get_moduli_sp_9d_from_dict()
