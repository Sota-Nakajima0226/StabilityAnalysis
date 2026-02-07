import sys
from pathlib import Path
from typing import List, Dict, Tuple
from sympy import Rational, Matrix, S

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from common.matrix_handler import SMH
from model.moduli import Moduli8DComponent, WilsonLine8DData
from model.massless_solution import LatticeElement9D, LatticeCoset9D


def get_moduli_8d_components_list(
    data: List[WilsonLine8DData], fund_weights: Dict[str, Matrix]
) -> List[List[Moduli8DComponent]]:
    def get_delta_component(
        removed_nodes: Dict[str, int], fund_weights: Dict[str, Matrix], order: int
    ) -> Matrix:
        vectors = []
        coefficients = []
        for l, s in removed_nodes.items():
            print(f"label, key: {l}, {s}")
            vectors.append(fund_weights[l])
            coefficients.append(Rational(s, order))
            print(f"fund_weight: {fund_weights[l]}")
            print(f"coefficient: {Rational(s, order)}")
            print(f"length: {len(fund_weights[l])}")
        return SMH.linear_combination(vectors=vectors, coefficients=coefficients)

    wl_list = []
    for wl8d in data:
        wl_components = []
        for coefficient in wl8d.coefficients:
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


def get_a8_and_b_from_delta(delta: Matrix, a9: Matrix) -> Tuple[Matrix, Rational]:
    a8 = Matrix(delta[2:, :])
    b = S(delta[0]) - SMH.dot_product(a9, a8) / S(2)
    return a8, Rational(b)


def classify_lattice_elements(
    lattice_9d: List[LatticeElement9D], delta: Matrix
) -> Tuple[List[LatticeCoset9D], List[LatticeElement9D]]:
    coset0 = []
    coset1 = []
    coset2 = []
    coset3 = []
    invalid_element = []
    for e in lattice_9d:
        e_pi = SMH.create_vector_from_str_list(e.pi)
        lattice_vector = SMH.extend_vector(e_pi, [e.w])
        inner_product = 4 * S(SMH.dot_product(delta, lattice_vector))
        if inner_product.q != 0:
            invalid_element.append(e)
            continue
        c = inner_product % 4
        if c == 0:
            coset0.append(e)
        elif c == 1:
            coset1.append(e)
        elif c == 2:
            coset2.append(e)
        elif c == 3:
            coset3.append(e)
    return [
        LatticeCoset9D(character=0, count=len(coset0), elements=coset0),
        LatticeCoset9D(character=1, count=len(coset1), elements=coset1),
        LatticeCoset9D(character=2, count=len(coset2), elements=coset2),
        LatticeCoset9D(character=3, count=len(coset3), elements=coset3),
    ], invalid_element
