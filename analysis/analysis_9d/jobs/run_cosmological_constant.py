from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_ROOT))

from analysis_9d.services.coset_service import classify_e16_by_a9
from sqlite.db_utils import (
    bulk_insert_e16_coset_9d,
    delete_records,
    select_moduli_9d,
    bulk_update_by_id,
    select_e16,
)
from config.env_settings import ENV
from config.logging_config import get_logger
from common.matrix_handler import SMH
from common.dynkin_handler import DH_E16
from model.lie_algebra import SemiSimpleLieAlg

log = get_logger("cosmological_const_9d")
debug = ENV.analysis_9d_debug
target_moduli_9d_ids = ENV.analysis_9d_target_moduli_9d_ids


def main():
    moduli_9d_list = select_moduli_9d(
        filtered_use_analysis_9d=True,
    )
    for moduli_9d in moduli_9d_list:
        if debug and moduli_9d.id not in target_moduli_9d_ids:
            continue
        log.info("Processing moduli_9d_id=%s where a9=%s", moduli_9d.id, moduli_9d.a9)
        a9 = SMH.create_vector_from_str_list(moduli_9d.a9)
        e16_roots = select_e16()
        coset0, coset1, coset2, coset3 = classify_e16_by_a9(moduli_9d.id, a9, e16_roots)
        gauge_group = SemiSimpleLieAlg(**moduli_9d.gauge_group)
        dimension = DH_E16.count_nonzero_roots(gauge_group)
        if dimension != len(coset0):
            log.error(
                "Dimension mismatch: dimension=%s, coset0=%s", dimension, len(coset0)
            )
            continue
        cosmological_constant = len(coset0) - len(coset2) + 24
        bulk_update_by_id(
            table_name="moduli_9d",
            update_data_list=[
                {"id": moduli_9d.id, "cosmological_constant": cosmological_constant}
            ],
        )
        delete_records(
            table_name="e16_coset_9d", conditions={"moduli_9d_id": moduli_9d.id}
        )
        bulk_insert_e16_coset_9d(coset0 + coset1 + coset2 + coset3)


if __name__ == "__main__":
    main()
