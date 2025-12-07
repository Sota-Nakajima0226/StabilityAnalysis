from pathlib import Path
from typing import List, Dict, Any
from sympy import Rational, Matrix

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.json_handler import JsonHandler
from common.matrix_handler import SMH, NMH
from common.file_path import EDD_PATH, INPUT_DIR_PATH

jh: JsonHandler = JsonHandler()
FUND_WEIGHTS_PATH: Path = INPUT_DIR_PATH / "fund_weights.json"
# coefficients in the linear combinations of the fundamental weights that give the candidates of the Wilson lines in 9D
COEFFICIENTS_JSON_PATH: Path = INPUT_DIR_PATH / "9d" / "coefficients.json"
COEFFICIENTS_DICT: List[dict] = jh.load_json(COEFFICIENTS_JSON_PATH)

FUND_WEIGHTS_DICT = jh.load_json(FUND_WEIGHTS_PATH)

EDD_DICT = jh.load_json(EDD_PATH)


def get_fund_weights_np() -> Dict[str, dict]:
    """
    Get fundamental weights of E8 x E8.

    Returns:
      dict: fundamental weights of E8 x E8:
        {
            "node label": {
                "vector": fundamental weight vector (np.ndarray),
                "k": Kac label (int)
            }, ...
        }
    """
    fund_weight_vectors = {}
    zero_vector = NMH.create_constant_vector(0.0)
    for label, fw in FUND_WEIGHTS_DICT.items():
        if int(label) < 10:
            fw_vector = NMH.concat_vectors(
                [NMH.create_vector(fw["components"]), zero_vector]
            )
        else:
            fw_vector = NMH.concat_vectors(
                [zero_vector, NMH.create_vector(fw["components"])]
            )
        if fw["den"] != 1:
            fw_vector = NMH.scalar_multiplication(
                vector=fw_vector, number=fw["den"], inverse=True
            )
        fund_weight_vectors[label] = {"vector": fw_vector, "k": fw["k"]}
    return fund_weight_vectors


FUND_WEIGHTS_NP = get_fund_weights_np()


def get_fund_weights_np_after_removing_nodes(removed_node_labels: List[str]) -> dict:
    """
    Get fundamental weights of a Dynkin diagram obtained from the EDD by removing two nodes.

    Args:
        removed_node_labels (List[str]): labels of removed nodes.

    Returns:
        dict: fundamental weights of the Dynkin diagram.
    """
    fw_dict = dict()
    for i in range(19):
        if i == 9:
            continue
        node_label = str(i)
        removed_node_label = removed_node_labels[0] if i < 9 else removed_node_labels[1]
        if node_label == removed_node_label:
            continue
        fund_weight = FUND_WEIGHTS_NP[node_label]
        removed_fund_weight = FUND_WEIGHTS_NP[removed_node_label]
        # first_term = removed_fund_weight["k"] * fund_weight["vector"]
        first_term = NMH.scalar_multiplication(
            vector=fund_weight["vector"], number=removed_fund_weight["k"]
        )
        # second_term = - fund_weight["k"] * NMH.create_vector(removed_fund_weight["vector"])
        second_term = NMH.scalar_multiplication(
            vector=NMH.create_vector(removed_fund_weight["vector"]),
            number=fund_weight["k"],
        )
        fw_vector = NMH.scalar_multiplication(
            vector=(first_term - second_term),
            number=removed_fund_weight["k"],
            inverse=True,
        )
        fw_dict[str(i)] = fw_vector
    fw_dict["-1"] = NMH.create_constant_vector(0.0, dimension=16).tolist()
    return fw_dict


from model.weight import FundWeightSp


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
    for node, fw in FUND_WEIGHTS_DICT.items():
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


from common.constants import EDD_JSON


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
