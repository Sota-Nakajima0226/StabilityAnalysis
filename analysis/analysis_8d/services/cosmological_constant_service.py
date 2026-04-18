import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


def get_cosmological_constant(
    massless_states_count: dict[int, dict[str, int]], moduli_8d_id: int
) -> int:
    states_count_dict = massless_states_count[moduli_8d_id]
    bosons_count = states_count_dict["bosons"]
    fermions_count = states_count_dict["fermions"]
    # the result value of the calculation
    value = 24 + bosons_count - fermions_count
    return value
