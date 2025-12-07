import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from common.json_handler import JSON_HANDLER
from common.file_path import EDD_PATH

# Keys of dictionary
KEY_COEFFS = "coefficients"
KEY_KAC_LABEL = "k"
KEY_VECTOR = "vector"

PRECISION = 10

EDD_JSON = JSON_HANDLER.load_json(EDD_PATH)
