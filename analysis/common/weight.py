from pathlib import Path
from typing import List, Dict
from sympy import Rational, Matrix

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.yaml_settings import YAML
from common.json_handler import JsonHandler
from common.matrix_handler import SMH
from common.dynkin_handler import EDD_JSON
from model.weight import FundWeightSp

jh: JsonHandler = JsonHandler()
FUND_WEIGHTS_PATH: Path = YAML.paths.input_dir / "fund_weights.json"


def get_fund_weights_sp_10d() -> Dict[str, FundWeightSp]:
    """
    Get fundamental weights of E8 x E8 by sympy.

    Returns:
      Dict[str, FundWeightSp]: fundamental weights of E8 x E8.
        key: node
        value: FundamentalWeight of the node
    """
    fund_weights = {}
    zero_vector = SMH.create_constant_vector(0)
    fund_weights_dict = jh.load_json(FUND_WEIGHTS_PATH)
    for node, fw in fund_weights_dict.items():
        if int(node) < 10:
            fw_vector = SMH.concat_vectors(
                [SMH.create_vector(fw["components"], fw["den"]), zero_vector]
            )
        else:
            fw_vector = SMH.concat_vectors(
                [zero_vector, SMH.create_vector(fw["components"], fw["den"])]
            )
        fund_weights[node] = FundWeightSp(vector=fw_vector, k=fw["k"])
    return fund_weights


FUND_WEIGHTS_SP_10D = get_fund_weights_sp_10d()


def get_fund_weights_sp_9d(removed_nodes: List[str]) -> Dict[str, Matrix]:
    """
    Get fundamental weights of a Dynkin diagram obtained from the EDD by removing two nodes.

    Args:
        removed_nodes (List[str]): labels of removed nodes.

    Returns:
        Dict[str,Matrix]: fundamental weights of the Dynkin diagram:
        hat{w}_l = w_l - (k_l / k_k) w_k,
        where k is a node removed by A9.
    """
    fw_dict = dict()
    for i in range(19):
        node = str(i)
        if i == 9:
            zero_vector_16d = SMH.create_constant_vector(0, dimension=16)
            fw_dict[node] = SMH.extend_vector(zero_vector_16d, [1, 0])
            continue
        removed_node = removed_nodes[0] if i < 9 else removed_nodes[1]
        if node == removed_node:  # Skip removed nodes
            continue
        fund_weight = FUND_WEIGHTS_SP_10D[node]
        removed_fund_weight = FUND_WEIGHTS_SP_10D[removed_node]
        c = Rational(fund_weight.k, removed_fund_weight.k)
        vector_16d = fund_weight.vector - c * removed_fund_weight.vector
        fw_dict[str(i)] = SMH.extend_vector(vector_16d, [0, 0])
    fw_dict["-1"] = SMH.create_constant_vector(0, dimension=18)
    return fw_dict


def get_roots_sp_9d(removed_nodes: List[str]) -> Dict[str, Matrix]:
    roots = dict()
    zero_vector_8d = SMH.create_constant_vector(0)
    for key, value in EDD_JSON.items():
        if key in removed_nodes:
            continue
        root_dict = value["root"]
        if int(key) < 9:
            vector_16d = SMH.concat_vectors(
                [
                    SMH.create_vector(root_dict["components"], root_dict["den"]),
                    zero_vector_8d,
                ]
            )
            root_vector = SMH.extend_vector(vector_16d, [0])
        elif int(key) > 9:
            vector_16d = SMH.concat_vectors(
                [
                    zero_vector_8d,
                    SMH.create_vector(root_dict["components"], root_dict["den"]),
                ]
            )
            root_vector = SMH.extend_vector(vector_16d, [0])
        else:
            root_vector = SMH.extend_vector(SMH.create_constant_vector(0, 16), [1])
        roots[key] = root_vector
    return roots


def check_fund_weights(removed_nodes: List[str]):
    fund_weights = get_fund_weights_sp_9d(removed_nodes)
    roots = get_roots_sp_9d(removed_nodes)
    result = dict()
    for i in range(19):
        if str(i) in removed_nodes:
            continue
        inner_prods = []
        root = roots[str(i)]
        for j in range(19):
            if str(j) in removed_nodes:
                continue
            fund_weight = fund_weights[str(j)]
            inner_prods.append(SMH.dot_product(root, fund_weight))
        result[str(i)] = inner_prods
    return result


if __name__ == "__main__":
    inner_prod_dict = check_fund_weights(["0", "18"])
    for key, value in inner_prod_dict.items():
        print(f"{key}: {value}")
