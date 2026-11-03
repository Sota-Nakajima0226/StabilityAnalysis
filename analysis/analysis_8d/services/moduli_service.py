import sys
import itertools
from pathlib import Path
from typing import List, Dict, Tuple
from sympy import Rational, Matrix

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.dynkin_handler import DH_E16
from model.lie_algebra import DynkinType, DynkinInfo, SemiSimpleLieAlg
from model.moduli import Coefficient, Moduli8DComponent
from common.matrix_handler import SMH

# Exhaustive A-series patterns: (order N, coefficient values on removed nodes).
_A_COEFFICIENT_PATTERNS: Tuple[Tuple[int, ...], ...] = (
    (1,),
    (1, 1),
    (3, 1),
    (2, 1, 1),
    (1, 1, 1, 1),
)


def find_coeffs_of_fund_weights_DE(
    extended_dynkin_info: DynkinInfo, kac_labels: Dict[str, int]
) -> List[Coefficient]:
    """
    Find coefficients of the fundamental weights to make Wilson lines in 8D as vectors of order 1, 2, or 4 in the lattice.

    Args:
        extended_dynkin_info (DynkinInfo): information of extended Dynkin diagram.
        kac_labels (dict): information of the Kac labels.
    Returns:
        List[Coefficient]: coefficients of the fundamental weights to make Wilson lines in 8D.
    """
    edd = extended_dynkin_info.diagram
    result: List[Coefficient] = []
    one_kac_labels = []
    two_kac_labels = []
    three_kac_labels = []
    four_kac_labels = []
    base_coefficients = dict()
    for node_label, kac_label in kac_labels.items():
        if kac_label == 1:
            one_kac_labels.append(node_label)
        if kac_label == 2:
            two_kac_labels.append(node_label)
        if kac_label == 3:
            three_kac_labels.append(node_label)
        if kac_label == 4:
            four_kac_labels.append(node_label)
        base_coefficients[node_label] = 0
    # N=1
    if len(one_kac_labels) > 0:
        for okl in one_kac_labels:
            coefficients = {**base_coefficients, okl: 1}
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [okl])
            )
            result.append(
                Coefficient(order=1, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )
    # N=2
    if len(two_kac_labels) > 0:
        for tkl in two_kac_labels:
            coefficients = {**base_coefficients, tkl: 1}
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [tkl])
            )
            result.append(
                Coefficient(order=2, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )
    if len(one_kac_labels) > 1:
        for okl1, okl2 in itertools.combinations(one_kac_labels, 2):
            coefficients = {**base_coefficients, okl1: 1, okl2: 1}
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [okl1, okl2])
            )
            result.append(
                Coefficient(order=2, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )
    # N=4
    # Notation: (coefficient, Kac label)
    # N = (1,4)
    if len(four_kac_labels) > 0:
        for fkl in four_kac_labels:
            coefficients = {**base_coefficients, fkl: 1}
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [fkl])
            )
            result.append(
                Coefficient(order=4, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )
    # N = (1,3) + (1,1)
    if len(three_kac_labels) > 0 and len(one_kac_labels) > 0:
        for thkl, okl in itertools.product(three_kac_labels, one_kac_labels):
            coefficients = {**base_coefficients, thkl: 1, okl: 1}
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [thkl, okl])
            )
            result.append(
                Coefficient(order=4, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )
    # N = (1,2) + (1,2)
    if len(two_kac_labels) > 1:
        for tkl1, tkl2 in itertools.combinations(two_kac_labels, 2):
            coefficients = {**base_coefficients, tkl1: 1, tkl2: 1}
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [tkl1, tkl2])
            )
            result.append(
                Coefficient(order=4, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )
    # N = (1,2) + (1,1) + (1,1)
    if len(two_kac_labels) > 0 and len(one_kac_labels) > 1:
        for tkl in two_kac_labels:
            for okl1, okl2 in itertools.combinations(one_kac_labels, 2):
                coefficients = {**base_coefficients, tkl: 1, okl1: 1, okl2: 1}
                lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                    DH_E16.remove_nodes(edd, [tkl, okl1, okl2])
                )
                result.append(
                    Coefficient(order=4, s=coefficients, lie_algebra_8d=lie_algebra_8d)
                )
    # N = (1,2) + (1,2)
    if len(two_kac_labels) > 0 and len(one_kac_labels) > 0:
        for tkl, okl in itertools.product(two_kac_labels, one_kac_labels):
            coefficients = {**base_coefficients, tkl: 1, okl: 2}
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [tkl, okl])
            )
            result.append(
                Coefficient(order=4, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )
    # N = (1,1) + (1,1) + (1,1) + (1,1)
    if len(one_kac_labels) > 3:
        for okl1, okl2, okl3, okl4 in itertools.combinations(one_kac_labels, 4):
            coefficients = {**base_coefficients, okl1: 1, okl2: 1, okl3: 1, okl4: 1}
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [okl1, okl2, okl3, okl4])
            )
            result.append(
                Coefficient(order=4, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )
    # N = (2,1) + (1,1) + (1,1)
    if len(one_kac_labels) > 2:
        for okl1, okl2, okl3 in itertools.combinations(one_kac_labels, 3):
            coefficients_list = [
                {**base_coefficients, okl1: 2, okl2: 1, okl3: 1},
                {**base_coefficients, okl1: 1, okl2: 2, okl3: 1},
                {**base_coefficients, okl1: 1, okl2: 1, okl3: 2},
            ]
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [okl1, okl2, okl3])
            )
            for coefficients in coefficients_list:
                result.append(
                    Coefficient(order=4, s=coefficients, lie_algebra_8d=lie_algebra_8d)
                )
    # N = (3,1) + (1,1)
    if len(one_kac_labels) > 1:
        for okl1, okl2 in itertools.combinations(one_kac_labels, 2):
            coefficients_list = [
                {**base_coefficients, okl1: 3, okl2: 1},
                {**base_coefficients, okl1: 1, okl2: 3},
            ]
            lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(
                DH_E16.remove_nodes(edd, [okl1, okl2])
            )
            for coefficients in coefficients_list:
                result.append(
                    Coefficient(order=4, s=coefficients, lie_algebra_8d=lie_algebra_8d)
                )
    return result


def find_coefficients_A(edd_info: DynkinInfo) -> List[Coefficient]:
    """
    Exhaustive A-series coefficients: all Kac-label-1 node combinations with
    orders 1, 2, 4 and patterns (1), (1,1), (3,1), (2,1,1), (1,1,1,1).
    """
    result: List[Coefficient] = []
    base_coefficients = {node: 0 for node in edd_info.diagram}
    for pattern in _A_COEFFICIENT_PATTERNS:
        set_coefficients_removed_nodes_A(
            extended_dynkin_info=edd_info,
            coefficient_list=result,
            base_coefficients=base_coefficients,
            coefficients_value=list(pattern),
        )
    return result


def set_coefficients_removed_nodes_A(
    extended_dynkin_info: DynkinInfo,
    coefficient_list: List[Coefficient],
    base_coefficients: Dict[str, int],
    coefficients_value: List[int],
) -> None:
    """
    Append coefficients for every choice of removed nodes with the given values.

    All distinct assignments of ``coefficients_value`` to the removed nodes are
    produced with ``set(itertools.permutations(...))``.
    """
    order = sum(coefficients_value)
    removed_nodes_num = len(coefficients_value)
    extended_diagram = extended_dynkin_info.diagram
    assignments = set(itertools.permutations(coefficients_value))
    for removed_nodes in itertools.combinations(
        extended_diagram.keys(), removed_nodes_num
    ):
        diagram_8d = DH_E16.remove_nodes(extended_diagram, list(removed_nodes))
        lie_algebra_8d = DH_E16.get_semi_simple_lie_algebra_from_diagram(diagram_8d)
        for values in assignments:
            coefficients = {**base_coefficients}
            for node, value in zip(removed_nodes, values):
                coefficients[node] = value
            coefficient_list.append(
                Coefficient(order=order, s=coefficients, lie_algebra_8d=lie_algebra_8d)
            )


def get_coefficients_8d(removed_nodes: List[str]) -> List[List[Coefficient]]:
    """
    For each connected component of the 9D Dynkin diagram, list the coefficient
    choices that build 8D Wilson lines.
    """
    result = []
    # Get the Dynkin diagram in 9D by removing the two node from the EDD
    diagram_9d = DH_E16.remove_nodes(DH_E16.diagram, removed_nodes)
    # Get the information of each connected diagram of the Dynkin diagram
    cdd_info_list_9d = DH_E16.get_connected_diagrams(diagram_9d)
    for cdd_info in cdd_info_list_9d:
        # Get Kac labels for each node of the connected Dynkin diagram
        kac_labels = DH_E16.get_kac_labels(cdd_info)
        # Add an extra node to the connected Dynkin diagram
        edd_info, kac_labels_edd = DH_E16.add_one_extra_node(
            dynkin_info=cdd_info, kac_labels=kac_labels
        )
        # Get coefficients of fundamental weights such that the linear combinations are Wilson lines for the twisted direction
        if cdd_info.type == DynkinType.A:
            coefficients = find_coefficients_A(edd_info=edd_info)
        else:
            coefficients = find_coeffs_of_fund_weights_DE(
                extended_dynkin_info=edd_info, kac_labels=kac_labels_edd
            )
        result.append(coefficients)
    return result


def get_moduli_8d_components_list(
    coefficients_list: List[List[Coefficient]], fund_weights: Dict[str, Matrix]
) -> List[List[Moduli8DComponent]]:
    def get_delta_component(
        removed_nodes: Dict[str, int], fund_weights: Dict[str, Matrix], order: int
    ) -> Matrix:
        vectors = []
        coefficients = []
        for l, s in removed_nodes.items():
            vectors.append(fund_weights[l])
            coefficients.append(Rational(s, order))
        return SMH.linear_combination(vectors=vectors, coefficients=coefficients)

    wl_list = []
    for coefficients in coefficients_list:
        wl_components = []
        for coefficient in coefficients:
            # Identify nodes removed by the A8.
            removed_nodes = {}
            for l, s in coefficient.s.items():
                if s == 0:
                    continue
                # nodes with nonzero coefficients correspond to removed ones
                removed_nodes[l] = s
            lie_alg = coefficient.lie_algebra_8d
            # Get the Wilson line as a linear combination of the fundamental weights with the coefficients
            delta = get_delta_component(removed_nodes, fund_weights, coefficient.order)
            wl_components.append(
                Moduli8DComponent(
                    removed_nodes_8d=list(removed_nodes.keys()),
                    lie_algebra_8d=lie_alg,
                    delta=delta,
                    coefficient=coefficient,
                )
            )
        wl_list.append(wl_components)
    return wl_list


def get_moduli_8d_info_from_components(
    moduli_tuple: tuple[Moduli8DComponent, ...],
) -> Tuple[Matrix, SemiSimpleLieAlg, List[str]]:
    delta = SMH.create_constant_vector(0, 18)
    lie_alg = SemiSimpleLieAlg()
    removed_nodes_8d = []
    for moduli in moduli_tuple:
        removed_nodes_8d.append(moduli.removed_nodes_8d)
        delta += moduli.delta
        if moduli.lie_algebra_8d.A:
            lie_alg.A.extend(moduli.lie_algebra_8d.A)
        if moduli.lie_algebra_8d.D:
            lie_alg.D.extend(moduli.lie_algebra_8d.D)
        if moduli.lie_algebra_8d.E:
            lie_alg.E.extend(moduli.lie_algebra_8d.E)
    return delta, lie_alg, removed_nodes_8d


def count_moduli_8d_candidates(removed_nodes: List[str]) -> int:
    """Number of moduli_8d rows for one moduli_9d background (product of choices)."""
    sizes = [len(c) for c in get_coefficients_8d(removed_nodes)]
    if not sizes:
        return 0
    total = 1
    for size in sizes:
        total *= size
    return total
