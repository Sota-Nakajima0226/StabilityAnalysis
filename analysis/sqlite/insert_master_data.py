from pathlib import Path
from dataclasses import asdict
import sys
import json

_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from common.matrix_handler import SMH
from common.lattice import E8_ROOTS_SP
from common.moduli import (
    generate_moduli_9d_from_coefficients,
    get_moduli_9d_max_enhancing_from_dict,
)
from sqlite.entities import E16, Moduli9d
from sqlite.db_utils import bulk_insert_e16, bulk_insert_moduli_9d


def insert_moduli_9d_max_enhancing():
    insert_data = []
    id = 1
    for mem in get_moduli_9d_max_enhancing_from_dict():
        a9 = mem.a9_1 + mem.a9_2
        a9_str = [str(e) for e in a9]
        insert_data.append(
            Moduli9d(
                id=1,
                removed_nodes=json.dumps(mem.removed_nodes),
                a9=json.dumps(a9_str),
                g9=str(mem.g9),
                gauge_group=json.dumps(asdict(mem.lie_algebra)),
                use_analysis_9d=0,
                cosmological_constant=None,
                is_critical_point=None,
                hessian=None,
                type=None,
            )
        )
        id += 1
    bulk_insert_moduli_9d(insert_data)


def insert_moduli_9d_from_coefficients():
    insert_data = []
    id = 1
    for mod in generate_moduli_9d_from_coefficients():
        a9 = mod.a9_1 + mod.a9_2
        a9_str = [str(e) for e in a9]
        insert_data.append(
            Moduli9d(
                id=id,
                removed_nodes=json.dumps(mod.removed_nodes),
                a9=json.dumps(a9_str),
                g9="",
                gauge_group=json.dumps(asdict(mod.lie_algebra)),
                use_analysis_9d=1,
                cosmological_constant=None,
                is_critical_point=None,
                hessian=None,
                type=None,
            )
        )
        id += 1
    bulk_insert_moduli_9d(insert_data)


def insert_e16():
    insert_data = []
    zero_vector_8 = SMH.create_constant_vector(0, 8)
    for root in E8_ROOTS_SP:
        element1_16 = SMH.concat_vectors([root, zero_vector_8])
        element1_str = [str(e) for e in element1_16]
        insert_data.append(E16(id=0, element=json.dumps(element1_str)))
    for root in E8_ROOTS_SP:
        element2_16 = SMH.concat_vectors([zero_vector_8, root])
        element2_str = [str(e) for e in element2_16]
        insert_data.append(E16(id=0, element=json.dumps(element2_str)))
    bulk_insert_e16(insert_data)


if __name__ == "__main__":
    insert_moduli_9d_max_enhancing()
    insert_moduli_9d_from_coefficients()
    insert_e16()
