"""
Reduced A-series coefficient enumeration (legacy).

Uses the circle symmetry of the extended Dynkin diagram of type A to keep only
representatives of each orbit. Kept for comparison with the exhaustive
enumeration in analysis_8d.services.moduli_service.
"""

import itertools
import sys
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from common.dynkin_handler import DH_E16
from model.lie_algebra import DynkinInfo
from model.moduli import Coefficient


def find_coefficients_A(edd_info: DynkinInfo) -> List[Coefficient]:
    result: List[Coefficient] = []
    diagram = edd_info.diagram
    base_coefficients = dict()
    for node in diagram:
        base_coefficients[node] = 0
    lie_algebras_8d = []
    # All Kac labels of A type are 1.
    # N=1
    # Remove one node
    diagram_8d = DH_E16.remove_nodes(diagram, ["-1"])
    lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(diagram_8d)
    lie_algebras_8d.append(lie_algebra_8d)
    coefficients = {**base_coefficients, "-1": 1}
    result.append(Coefficient(order=1, s=coefficients, lie_algebra_8d=lie_algebra_8d))
    # Remove two nodes
    if edd_info.rank > 1:
        # N=2
        set_coefficients_two_nodes_A(
            extended_dynkin_info=edd_info,
            coefficient_list=result,
            base_coefficients=base_coefficients,
        )
        # N=4
        set_coefficients_two_nodes_A(
            extended_dynkin_info=edd_info,
            coefficient_list=result,
            base_coefficients=base_coefficients,
            value1=3,
        )
    # Remove three nodes
    if edd_info.rank > 2:
        # N=4
        set_coefficients_multiple_nodes_A(
            extended_dynkin_info=edd_info,
            coefficient_list=result,
            base_coefficients=base_coefficients,
            num_removed_nodes=3,
            reference_node_value=2,
        )
    # Remove four nodes
    if edd_info.rank > 3:
        # N=4
        set_coefficients_multiple_nodes_A(
            extended_dynkin_info=edd_info,
            coefficient_list=result,
            base_coefficients=base_coefficients,
            num_removed_nodes=4,
        )
    return result


def set_coefficients_two_nodes_A(
    extended_dynkin_info: DynkinInfo,
    coefficient_list: List[Coefficient],
    base_coefficients: Dict[str, int],
    reference_node: str = "-1",
    value1: int = 1,
    value2: int = 1,
):
    order = value1 + value2
    previous_removed_node = reference_node
    diagram = extended_dynkin_info.diagram
    removed_node = diagram[previous_removed_node][0]
    for _ in range(1, extended_dynkin_info.rank // 2 + 1):
        removed_nodes = [reference_node, removed_node]
        diagram_after_removing_nodes = DH_E16.remove_nodes(diagram, removed_nodes)
        coefficients = {
            **base_coefficients,
            reference_node: value1,
            removed_node: value2,
        }
        coefficient_list.append(
            Coefficient(
                order=order,
                s=coefficients,
                lie_algebra_8d=DH_E16.get_semi_simple_lie_algebra_from_diagram(
                    diagram_after_removing_nodes
                ),
            )
        )
        next_removed_node = next(
            (l for l in diagram[removed_node] if l != previous_removed_node), None
        )
        if not next_removed_node:
            break
        previous_removed_node = removed_node
        removed_node = next_removed_node


def set_coefficients_multiple_nodes_A(
    extended_dynkin_info: DynkinInfo,
    coefficient_list: List[Coefficient],
    base_coefficients: Dict[str, int],
    num_removed_nodes: int,
    reference_node: str = "-1",
    reference_node_value: int = 1,
    other_nodes_value: int = 1,
):
    order = reference_node_value + other_nodes_value * (num_removed_nodes - 1)
    extended_diagram = extended_dynkin_info.diagram
    diagram_a = DH_E16.remove_nodes(extended_diagram, [reference_node])
    lie_algebras_8d = []
    for removed_nodes in itertools.combinations(
        diagram_a.keys(), num_removed_nodes - 1
    ):
        diagram_8d = DH_E16.remove_nodes(diagram_a, list(removed_nodes))
        semi_simple_lie_algebra = DH_E16.get_semi_simple_lie_algebra_from_diagram(
            diagram_8d
        )
        if semi_simple_lie_algebra not in lie_algebras_8d:
            lie_algebras_8d.append(semi_simple_lie_algebra)
            coefficients = {**base_coefficients, reference_node: reference_node_value}
            for rn in removed_nodes:
                coefficients[rn] = other_nodes_value
            coefficient_list.append(
                Coefficient(
                    order=order, s=coefficients, lie_algebra_8d=semi_simple_lie_algebra
                )
            )
