import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.moduli import generate_moduli_9d_from_coefficients 

print(generate_moduli_9d_from_coefficients())