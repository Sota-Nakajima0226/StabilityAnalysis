import sys
import itertools
import json
from pathlib import Path
from typing import List, cast
from dataclasses import asdict
from sympy import Matrix, Rational, sqrt, floor, ceiling, S

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.lattice import E8_ROOTS_SP
from common.dynkin_handler import DH_E16
from common.json_handler import JSON_HANDLER
import common.file_path as fp
from common.matrix_handler import SMH
from model.moduli import Moduli9DOutput
from model.lie_algebra import SemiSimpleLieAlg
from model.massless_solution import LatticeElement9D, MasslessSolution9D
from sqlite.db_utils import (
    select_moduli_9d,
    bulk_insert_massless_solution_9d,
    delete_records,
)
from sqlite.entities import MasslessSolution9d


############
# Settings
############
# removed nodes excluded from the calculation
skip_nodes = [["8", "18"]]
# if output the results to json files
is_output_file = False
# if the execution mode is debug
debug = False
# calculation targets in debug mode
target_removed_nodes = [["6", "10"]]


def solve_massless_conditions_9d(
    moduli_9d_id: int, a_1: Matrix, a_2: Matrix, g: Rational
) -> List[MasslessSolution9d]:
    result = []
    a = a_1 + a_2
    r_inverse = 1 / S(sqrt(g))
    floor_r_inverse = S(floor(r_inverse))
    for w in range(-floor_r_inverse, floor_r_inverse + 1):
        if w == 0:  # Find non-winding solutions
            find_non_winding_solutions(
                solutions=result, moduli_9d_id=moduli_9d_id, a_1=a_1, a_2=a_2
            )
        else:
            rhs = 2 - 2 * (w**2) * S(g)
            ranges1_o = []
            ranges1_s = []
            ranges2_o = []
            ranges2_s = []
            # Determine the bounds of each component of lattice elements
            for i in range(16):
                upper_bound = sqrt(rhs) - w * a[i]
                lower_bound = -sqrt(rhs) - w * a[i]
                # Range for the scalar conjugacy class
                range_o = range(S(ceiling(lower_bound)), S(floor(upper_bound)) + 1)
                # Range for the spinor conjugacy class
                range_s = range(
                    S(ceiling(lower_bound - Rational(1, 2))),
                    S(floor(upper_bound - Rational(1, 2))) + 1,
                )
                if i < 8:
                    ranges1_o.append(range_o)
                    ranges1_s.append(range_s)
                else:
                    ranges2_o.append(range_o)
                    ranges2_s.append(range_s)
            # Solutions in OO class
            find_winding_solutions(
                solutions=result,
                moduli_9d_id=moduli_9d_id,
                rhs=rhs,
                a_1=a_1,
                a_2=a_2,
                w=w,
                ranges1=ranges1_o,
                ranges2=ranges2_o,
                spin1=False,
                spin2=False,
            )
            # Solutions in OS class
            find_winding_solutions(
                solutions=result,
                moduli_9d_id=moduli_9d_id,
                rhs=rhs,
                a_1=a_1,
                a_2=a_2,
                w=w,
                ranges1=ranges1_o,
                ranges2=ranges2_s,
                spin1=False,
                spin2=True,
            )
            # Solutions in SO class
            find_winding_solutions(
                solutions=result,
                moduli_9d_id=moduli_9d_id,
                rhs=rhs,
                a_1=a_1,
                a_2=a_2,
                w=w,
                ranges1=ranges1_s,
                ranges2=ranges2_o,
                spin1=True,
                spin2=False,
            )
            # Solutions in SS class
            find_winding_solutions(
                solutions=result,
                moduli_9d_id=moduli_9d_id,
                rhs=rhs,
                a_1=a_1,
                a_2=a_2,
                w=w,
                ranges1=ranges1_s,
                ranges2=ranges2_s,
                spin1=True,
                spin2=True,
            )
    return result


def find_non_winding_solutions(
    solutions: List[MasslessSolution9d], moduli_9d_id: int, a_1: Matrix, a_2: Matrix
):
    zero_vector_8d = SMH.create_constant_vector(0)
    for pi in E8_ROOTS_SP:
        pi1 = SMH.concat_vectors([pi, zero_vector_8d])
        n1 = SMH.dot_product(pi1, a_1)
        # (w, n, Pi) is a solution if n is an integer
        if n1.q == 1:
            element = [str(0), str(int(n1))] + [str(e) for e in pi1]
            solutions.append(
                MasslessSolution9d(
                    id=0, moduli_9d_id=moduli_9d_id, element=json.dumps(element)
                )
            )
        pi2 = SMH.concat_vectors([zero_vector_8d, pi])
        n2 = SMH.dot_product(pi2, a_2)
        # (w, n, Pi) is a solution if n is an integer
        if n2.q == 1:
            element = [str(0), str(int(n2))] + [str(e) for e in pi2]
            solutions.append(
                MasslessSolution9d(
                    id=0, moduli_9d_id=moduli_9d_id, element=json.dumps(element)
                )
            )


def find_winding_solutions(
    solutions: List[MasslessSolution9d],
    moduli_9d_id: int,
    rhs: Rational,
    a_1: Matrix,
    a_2: Matrix,
    w: int,
    ranges1: List[range],
    ranges2: List[range],
    spin1: bool,
    spin2: bool,
):
    """
    Find winding solutions by solving the conditions:
        (Pi + wA)^2 = 2 - 2(w^2R^2).
        n = w + Pi /dot A is an integer.
    """
    zero_vector = SMH.create_constant_vector(0)
    for pi1 in itertools.product(*ranges1):
        pi1 = SMH.create_vector(list(pi1))
        # Skip if pi1 is not an element of the E8 root lattice
        if sum(S(pi1)) % 2 != 0:
            continue
        if spin1:
            # Shift by a half vector for an element in the spinor conjugacy class
            pi1 = pi1 + SMH.create_constant_vector(Rational(1, 2))
        pi1 = SMH.concat_vectors([pi1, zero_vector])
        v1 = pi1 + w * a_1
        lhs1 = SMH.dot_product(v1, v1)
        if lhs1 > rhs:
            # Skip if l.h.s is greater than r.h.s
            continue
        for pi2 in itertools.product(*ranges2):
            pi2 = SMH.create_vector(list(pi2))
            if sum(S(pi2)) % 2 != 0:
                continue
            if spin2:
                pi2 = pi2 + SMH.create_constant_vector(Rational(1, 2))
            pi2 = SMH.concat_vectors([zero_vector, pi2])
            v2 = pi2 + w * a_2
            lhs2 = SMH.dot_product(v2, v2)
            lhs = S(lhs1) + S(lhs2)
            if lhs != rhs:
                continue
            n = w + S(SMH.dot_product(pi1, a_1)) + S(SMH.dot_product(pi2, a_2))
            if n.q == 1:
                element = [str(int(w)), str(int(n))] + [str(e) for e in (pi1 + pi2)]
                solutions.append(
                    MasslessSolution9d(
                        id=0, moduli_9d_id=moduli_9d_id, element=json.dumps(element)
                    )
                )


def main():
    fp.MASSLESS_SOLUTION_SP_9D_DIR_PATH.mkdir(parents=True, exist_ok=True)
    invalid_results = []
    zero_vector_8d = SMH.create_constant_vector(0)
    moduli_9d_list = select_moduli_9d()
    for m9 in moduli_9d_list:
        removed_nodes = list(m9.removed_nodes)
        if removed_nodes in skip_nodes:
            continue
        if debug and removed_nodes not in target_removed_nodes:
            continue
        print(
            f"Solving the massless conditions in 9D for removed_nodes={removed_nodes}..."
        )
        a9_1_8d = SMH.create_vector_from_str_list(m9.a9[:8])
        a9_2_8d = SMH.create_vector_from_str_list(m9.a9[8:])
        a9_1 = SMH.concat_vectors([a9_1_8d, zero_vector_8d])
        a9_2 = SMH.concat_vectors([zero_vector_8d, a9_2_8d])
        g9 = Rational(m9.g9)
        # Solve massless conditions with the moduli in 9D
        massless_solutions = solve_massless_conditions_9d(
            moduli_9d_id=m9.id, a_1=a9_1, a_2=a9_2, g=g9
        )
        # Check if the number of solutions matches the dimension of gauge group
        gauge_group = SemiSimpleLieAlg(**cast(dict, m9.gauge_group))
        is_valid = len(massless_solutions) == DH_E16.count_nonzero_roots(gauge_group)
        if is_valid:
            # Delete previous results before inserting new results
            delete_records(
                table_name="massless_solution_9d", conditions={"moduli_9d_id": m9.id}
            )
            # Insert the calculation results
            bulk_insert_massless_solution_9d(massless_solutions)
            # Output the result to a json file if is_output_file is True
            if is_output_file:
                moduli_output = Moduli9DOutput(
                    removed_nodes=removed_nodes,
                    a9_1=[str(e) for e in a9_1],
                    a9_2=[str(e) for e in a9_2],
                    g9=str(m9.g9),
                    lie_algebra=gauge_group,
                )
                output_result = MasslessSolution9D(
                    moduli=moduli_output,
                    count_solutions=len(massless_solutions),
                    is_valid=is_valid,
                    solutions=[
                        LatticeElement9D(
                            w=s.element[0],
                            n=s.element[1],
                            pi=[str(e) for e in s.element[2:]],
                        )
                        for s in massless_solutions
                    ],
                )
                file_path = (
                    fp.MASSLESS_SOLUTION_SP_9D_DIR_PATH
                    / f"{removed_nodes[0]}-{removed_nodes[1]}.json"
                )
                JSON_HANDLER.save_json(asdict(output_result), file_path)
        else:
            print(f"Invalid result: {m9.removed_nodes}")
            invalid_results.append((m9.removed_nodes, massless_solutions))
    if len(invalid_results) == 0:
        print("All calculations are consistent with the expected results")
    else:
        print("The following calculations are inconsistent with the expected results:")
        for ir in invalid_results:
            print(ir[0])
            file_path = (
                fp.MASSLESS_SOLUTION_SP_9D_DIR_PATH
                / "invalid_results"
                / f"{ir[0][0]}-{ir[0][1]}.json"
            )
            JSON_HANDLER.save_json(asdict(ir[1]), file_path)


if __name__ == "__main__":
    main()
