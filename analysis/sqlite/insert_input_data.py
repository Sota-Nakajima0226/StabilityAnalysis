from pathlib import Path
from dataclasses import asdict
import sys
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))
from sqlite.entities import Moduli9d
from sqlite.db_utils import bulk_insert_moduli_9d
from common.moduli import MAX_ENHANCING_MODULI_SP_9D


def insert_moduli_9d():
    insert_data = []
    id = 1
    for mem in MAX_ENHANCING_MODULI_SP_9D:
        a9 = mem.a9_1 + mem.a9_2
        a9_str = [str(e) for e in a9]
        insert_data.append(
            Moduli9d(
                id=1,
                removed_nodes=json.dumps(mem.removed_nodes),
                a9=json.dumps(a9_str),
                g9=str(mem.g9),
                gauge_group=json.dumps(asdict(mem.lie_algebra)),
                maximal_enhanced=1,
                cosmological_constant=None,
                is_critical_point=None,
                hessian=None,
                type=None,
            )
        )
        id += 1
    bulk_insert_moduli_9d(insert_data)


if __name__ == "__main__":
    insert_moduli_9d()
