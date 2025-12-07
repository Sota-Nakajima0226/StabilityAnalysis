import sys
import itertools
from pathlib import Path
from typing import List, Tuple, Optional
from sympy import Matrix, pi, cos, S, Rational
from dataclasses import asdict
from dacite import from_dict, Config

from utils import get_moduli_8d_components_list, get_a8_and_b_from_delta

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from common.json_handler import JSON_HANDLER
import common.file_path as fp
from common.dynkin_handler import DH_E16
import common.constants as const
from common.matrix_handler import SMH
from common.weight import get_fund_weights_sp_9d
from model.massless_solution import MasslessSolution9D, LatticeElement9D
from model.moduli import WilsonLine8D, Moduli8D
from model.cosmological_constant import CosmologicalConst8D
from model.lie_algebra import SemiSimpleLieAlg, DynkinType

RESULT_DIR_PATH = fp.CC_SP_8D_DIR_PATH
MAX_N: int = 3


def get_lattice_8d_sum(
    n: int,
    lattice_9d: List[LatticeElement9D],
    delta: Matrix,
) -> Tuple[float, int, bool, dict]:
    result = S(0)
    massless_boson_count = 0
    contain_invalid_result = False
    boson_list = []
    fermion_list = []
    others = []
    for e in lattice_9d:
        e_pi = SMH.create_vector_from_str_list(e.pi)
        lattice_vector = SMH.extend_vector(e_pi, [e.w])
        inner_product = SMH.dot_product(delta, lattice_vector)
        arg = S(2 * (2 * n - 1)) * inner_product
        cosine = cos(pi * arg)
        if S(cosine).is_integer:
            dict = {
                "vector": [str(e) for e in lattice_vector],
                "inner_prod": str(inner_product),
            }
            if cosine == 1:
                massless_boson_count += 1
                boson_list.append(dict)
            elif cosine == -1:
                fermion_list.append(dict)
            elif cosine == 0:
                others.append(dict)
        elif not contain_invalid_result:
            # the value of cosine must be an integer for valid input
            contain_invalid_result = True
        result += cosine
    # print("==Bosonic States==")
    # for b in boson_list:
    #     print(b)
    # print("==Fermionic States==")
    # for f in fermion_list:
    #     print(f)
    # print("==Others==")
    # for o in others:
    #     print(o)
    num_states = len(boson_list) + len(fermion_list) + len(others)
    states_dict = {
        "delta": [str(e) for e in delta],
        "bosons": boson_list,
        "ferminons": fermion_list,
        "others": others,
        "num_states": num_states,
    }
    # print(f"The number of bosons: {len(boson_list)}")
    # print(f"The number of ferminons: {len(fermion_list)}")
    # print(f"The number of others: {len(others)}")
    print(f"The number of states: {num_states}")
    return result, massless_boson_count, contain_invalid_result, states_dict


debug = True
N_MAX = 2
target_wl_files = [
    "6-16.json",
    # "1-18.json",
    # "2-15.json"
    # "3-15.json",
    # "4-15.json",
    # "5-10.json",
    # "5-15.json",
    # "5-16.json",
    # "5-18.json",
    # "7-15.json",
]


def main():
    fp.CC_SP_8D_DIR_PATH.mkdir(parents=True, exist_ok=True)
    # Read json files
    wilson_line_files = JSON_HANDLER.get_json_files_by_pattern(
        dir_path=fp.WL_8D_DIR_PATH, pattern=r"^\d+-\d+\.json$"
    )
    suppressed_cc_list = []
    invalid_results = []
    for wlf in wilson_line_files:
        result = []
        if debug and wlf not in target_wl_files:
            continue
        print(f"wilson line file: {wlf}")
        # Load massless solutions in 9D from the json file.
        massless_solutions_9d = from_dict(
            MasslessSolution9D,
            JSON_HANDLER.load_json(fp.MASSLESS_SOLUTION_SP_9D_DIR_PATH / wlf),
        )
        solutions_9d = massless_solutions_9d.solutions
        a9_1 = SMH.create_vector_from_str_list(massless_solutions_9d.moduli.a9_1)
        a9_2 = SMH.create_vector_from_str_list(massless_solutions_9d.moduli.a9_2)
        a9 = a9_1 + a9_2
        g9 = massless_solutions_9d.moduli.g9
        print(f"wilson_line_8d file path: {fp.WL_8D_DIR_PATH / wlf}")
        # Load Wilson Line data from the json file
        config = Config(type_hooks={DynkinType: DynkinType})
        wl_8d = from_dict(
            WilsonLine8D, JSON_HANDLER.load_json(fp.WL_8D_DIR_PATH / wlf), config=config
        )
        # Get fundamental weights in 9D
        fund_weights_9d = get_fund_weights_sp_9d(wl_8d.removed_nodes_9d)
        moduli_components_list = get_moduli_8d_components_list(
            wl_8d.data, fund_weights_9d
        )
        i = 0
        states_dict_list = []
        for moduli_tuple in list(itertools.product(*moduli_components_list)):
            if "9" not in moduli_tuple[1].removed_nodes_8d:
                continue
            i += 1
            # if debug and i < 31:
            #     continue
            delta = SMH.create_constant_vector(0, 17)
            lie_alg = SemiSimpleLieAlg()
            removed_nodes_8d = []
            coefficients_8d = []
            for moduli in moduli_tuple:
                removed_nodes_8d.append(moduli.removed_nodes_8d)
                coefficients_8d.append(asdict(moduli.coefficient))
                delta += moduli.delta
                if moduli.lie_algebra_8d.A:
                    lie_alg.A.extend(moduli.lie_algebra_8d.A)
                if moduli.lie_algebra_8d.D:
                    lie_alg.D.extend(moduli.lie_algebra_8d.D)
                if moduli.lie_algebra_8d.E:
                    lie_alg.E.extend(moduli.lie_algebra_8d.E)
            # print("Moduli vector in 8D:")
            # print(delta)
            # print("Lie algebra:")
            # print(lie_alg)
            a8, b = get_a8_and_b_from_delta(delta, a9)
            lattice_sum, massless_boson_count, invalid_result, states_dict = (
                get_lattice_8d_sum(
                    n=1,
                    lattice_9d=solutions_9d,
                    delta=delta,
                )
            )
            # print("lattice sum:")
            # print(lattice_sum)
            value = lattice_sum + 24.0
            cc8 = CosmologicalConst8D(
                removed_nodes_9d=wl_8d.removed_nodes_9d,
                removed_nodes_8d=removed_nodes_8d,
                moduli=Moduli8D(
                    a8=[str(e) for e in a8],
                    a9=[str(e) for e in a9],
                    g9=str(g9),
                    b=str(b),
                    e21=str(delta[0]),
                ),
                semi_simple_lie_alg=lie_alg,
                massless_boson_count=massless_boson_count,
                lattice_sum=int(lattice_sum),
                value=int(value),
                is_suppressed=False,
                is_valid=True,
            )
            num_nonzero_roots = DH_E16.count_nonzero_roots(lie_alg)
            states_dict_list.append(
                {
                    "removed_nodes_8d": removed_nodes_8d,
                    "coefficients_8d": coefficients_8d,
                    "semi_simple_lie_alg": asdict(lie_alg),
                    "massless_boson_count": massless_boson_count,
                    "num_nonzero_roots": num_nonzero_roots,
                    "is_valid": massless_boson_count == num_nonzero_roots,
                    "states": states_dict,
                }
            )
            if num_nonzero_roots != massless_boson_count or invalid_result:
                cc8.is_valid = False
                print("!!!INVALID RESULT!!!")
                for moduli in moduli_tuple:
                    print(f"coefficient: {moduli.coefficient}")
                    print(f"removed nodes 8D: {moduli.removed_nodes_8d}")
                    print(f"Lie algebra 8D: {moduli.lie_algebra_8d}")
                print("number of massless bosons:")
                print(massless_boson_count)
                print("The number of nonzero roots:")
                print(num_nonzero_roots)
                print("result:")
                print(cc8)
                # JSON_HANDLER.save_json(data=states_dict, file_path=fp.CC_SP_8D_DIR_PATH / "states" / f"{wlf}")
                invalid_results.append(asdict(cc8))
            if value == 0:
                cc8.is_suppressed = True
                suppressed_cc_list.append(asdict(cc8))
            result.append(asdict(cc8))
            if debug and i > 100:
                break
        JSON_HANDLER.save_json(data=result, file_path=fp.CC_SP_8D_DIR_PATH / f"{wlf}")
        JSON_HANDLER.save_json(
            data=states_dict_list, file_path=fp.CC_SP_8D_DIR_PATH / "states" / f"{wlf}"
        )
    if len(suppressed_cc_list) > 0:
        print("!!!There are suppressed cosmological constants!!!")
        JSON_HANDLER.save_json(
            data=suppressed_cc_list,
            file_path=fp.CC_SP_8D_DIR_PATH / "suppressed_cc.json",
        )
    else:
        print("There are NO suppressed cosmological constants")
    if len(invalid_results) > 0:
        print("!!!There are invalid calculations!!!")
        JSON_HANDLER.save_json(
            data=invalid_results,
            file_path=fp.CC_SP_8D_DIR_PATH / "invalid_results.json",
        )
    else:
        print("!!!All calculations are valid!!!")


a8 = [
    "0",
    "0",
    "0",
    "0",
    "0",
    "0",
    "0",
    "0",
    "3/8",
    "1/8",
    "1/8",
    "1/8",
    "1/8",
    "1/8",
    "1/8",
    "-1/8",
]
a9 = ["0", "0", "0", "0", "0", "0", "0", "0", "-1", "0", "0", "0", "0", "0", "0", "0"]
b = Rational(7, 16)


def call_get_lattice_sum(wl_file_name: str):
    a9_vec = SMH.create_vector_from_str_list(a9)
    a8_vec = SMH.create_vector_from_str_list(a8)
    delta_0 = b + SMH.dot_product(a9_vec, a8_vec) / S(2)
    print(f"delta_0: {delta_0}")
    delta = SMH.extend_vector(a8_vec, [delta_0])
    massless_solutions_9d = from_dict(
        MasslessSolution9D,
        JSON_HANDLER.load_json(
            fp.MASSLESS_SOLUTION_SP_9D_DIR_PATH / f"{wl_file_name}.json"
        ),
    )
    solutions_9d = massless_solutions_9d.solutions
    lattice_sum, massless_boson_count, _, _ = get_lattice_8d_sum(
        n=1,
        lattice_9d=solutions_9d,
        delta=delta,
    )
    print(f"Lattice sum: {lattice_sum}")
    print(f"Massless boson count: {massless_boson_count}")


if __name__ == "__main__":
    main()
    # call_get_lattice_sum("0-18")
