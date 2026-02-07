import sys
from pathlib import Path
from dataclasses import asdict

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.json_handler import JSON_HANDLER
import common.file_path as fp
from sqlite.db_utils import (
    select_moduli_8d,
    bulk_update_by_id,
    get_massless_states_count_from_coset_8d,
)

############
# Settings
############
# if the execution mode is debug
debug = False
# calculation targets in debug mode
target_moduli_9d_ids = [1]
# chunk size of records in moduli_8d
chunk_size = 5000


def main():
    offset = 0
    moduli_8d_with_suppressed_cc = []
    print("Counting massless states...")
    massless_states_count = get_massless_states_count_from_coset_8d()
    while True:
        # get moduli_8d
        moduli_8d_list = select_moduli_8d(limit=chunk_size, offset=offset)
        if not moduli_8d_list:
            break
        update_data_list = []
        for moduli_8d in moduli_8d_list:
            if debug and moduli_8d.moduli_9d_id not in target_moduli_9d_ids:
                continue
            print(f"removed nodes by moduli_8d: {moduli_8d.removed_nodes}")
            states_count_dict = massless_states_count[moduli_8d.id]
            bosons_count = states_count_dict["bosons"]
            fermions_count = states_count_dict["fermions"]
            # the result value of the calculation
            value = 24 + bosons_count - fermions_count
            update_data_list.append(
                {"id": moduli_8d.id, "cosmological_constant": value}
            )
            if value == 0:
                moduli_8d.cosmological_constant = value
                moduli_8d_with_suppressed_cc.append(asdict(moduli_8d))
        # bulk update
        bulk_update_by_id(table_name="moduli_8d", update_data_list=update_data_list)
        offset += chunk_size
    print("All calculations completed successfully")
    if moduli_8d_with_suppressed_cc:
        JSON_HANDLER.save_json(
            data=moduli_8d_with_suppressed_cc,
            file_path=fp.CC_SP_8D_DIR_PATH / "suppressed_cc.json",
        )
        print(
            f"There are {len(moduli_8d_with_suppressed_cc)} moduli with suppressed cosmological constant:"
        )
        for m8 in moduli_8d_with_suppressed_cc:
            print(m8)


if __name__ == "__main__":
    main()
