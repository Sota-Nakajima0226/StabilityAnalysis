from pathlib import Path

# input file path
INPUT_DIR_PATH = Path(__file__).resolve().parent.parent.parent / "input"
EDD_PATH: Path = INPUT_DIR_PATH / "edd.json"

# result file path for 9D model analysis
OUTPUT_9D_DIR_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent / "output" / "9d"
)
OUTPUT_NP_9D_DIR_PATH: Path = OUTPUT_9D_DIR_PATH / "np"
OUTPUT_SP_9D_DIR_PATH: Path = OUTPUT_9D_DIR_PATH / "sp"
CC_NP_9D_DIR_PATH: Path = OUTPUT_NP_9D_DIR_PATH / "cosmological_const"
CC_SP_9D_DIR_PATH: Path = OUTPUT_SP_9D_DIR_PATH / "cosmological_const"
SUPPRESSED_CC_NP_9D_FILE_PATH: Path = CC_NP_9D_DIR_PATH / "suppressed_cc.json"
SUPPRESSED_CC_SP_9D_FILE_PATH: Path = CC_SP_9D_DIR_PATH / "suppressed_cc.json"
FD_NP_9D_DIR_PATH: Path = OUTPUT_NP_9D_DIR_PATH / "first_derivative"
FD_SP_9D_DIR_PATH: Path = OUTPUT_SP_9D_DIR_PATH / "first_derivative"
CRITICAL_POINTS_NP_9D_FILE_PATH: Path = FD_NP_9D_DIR_PATH / "critical_points.json"
CRITICAL_POINTS_SP_9D_FILE_PATH: Path = FD_SP_9D_DIR_PATH / "critical_points.json"
SD_NP_9D_DIR_PATH: Path = OUTPUT_NP_9D_DIR_PATH / "second_derivative"
SD_SP_9D_DIR_PATH: Path = OUTPUT_SP_9D_DIR_PATH / "second_derivative"
MASSLESS_SOLUTION_NP_9D_DIR_PATH: Path = OUTPUT_NP_9D_DIR_PATH / "massless_solution"
MASSLESS_SOLUTION_SP_9D_DIR_PATH: Path = OUTPUT_SP_9D_DIR_PATH / "massless_solution"
MINIMA_NP_9D_FILE_PATH: Path = SD_NP_9D_DIR_PATH / "minima.json"
MINIMA_SP_9D_FILE_PATH: Path = SD_SP_9D_DIR_PATH / "minima.json"
MAXIMA_NP_9D_FILE_PATH: Path = SD_NP_9D_DIR_PATH / "maxima.json"
MAXIMA_SP_9D_FILE_PATH: Path = SD_SP_9D_DIR_PATH / "maxima.json"

# result file path for 8D model analysis
OUTPUT_8D_DIR_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent / "output" / "8d"
)
WL_8D_DIR_PATH: Path = OUTPUT_8D_DIR_PATH / "wilson_line"
OUTPUT_NP_8D_DIR_PATH: Path = OUTPUT_8D_DIR_PATH / "np"
OUTPUT_SP_8D_DIR_PATH: Path = OUTPUT_8D_DIR_PATH / "sp"
CC_NP_8D_DIR_PATH: Path = OUTPUT_NP_8D_DIR_PATH / "cosmological_const"
CC_SP_8D_DIR_PATH: Path = OUTPUT_SP_8D_DIR_PATH / "cosmological_const"
SUPPRESSED_CC_NP_8D_FILE_PATH: Path = CC_NP_8D_DIR_PATH / "suppressed_cc.json"
SUPPRESSED_CC_SP_8D_FILE_PATH: Path = CC_SP_8D_DIR_PATH / "suppressed_cc.json"


# CC_9D_DIR_PATH: Path = OUTPUT_9D_DIR_PATH / "cosmological_const"
# SUPPRESSED_CC_9D_FILE_PATH: Path = CC_9D_DIR_PATH / "suppressed_cc.json"
# FD_9D_DIR_PATH: Path = OUTPUT_9D_DIR_PATH / "first_derivative"
# CRITICAL_POINTS_9D_FILE_PATH: Path = FD_9D_DIR_PATH / "critical_points.json"
# SD_9D_DIR_PATH: Path = OUTPUT_9D_DIR_PATH / "second_derivative"
# MASSLESS_SOLUTION_9D_DIR_PATH: Path = OUTPUT_9D_DIR_PATH / "massless_solution"
# MINIMA_9D_FILE_PATH: Path = SD_9D_DIR_PATH / "minima.json"
# MAXIMA_9D_FILE_PATH: Path = SD_9D_DIR_PATH / "maxima.json"
# result file path for 8D model analysis by numpy
# OUTPUT_8D_DIR_PATH: Path = Path(__file__).resolve().parent.parent / "output" / "8d"
# WL_8D_DIR_PATH: Path = OUTPUT_8D_DIR_PATH / "wilson_line"
# CC_8D_DIR_PATH: Path = OUTPUT_8D_DIR_PATH / "cosmological_const"
# SUPPRESSED_CC_8D_FILE_PATH: Path = CC_8D_DIR_PATH / "suppressed_cc.json"

# result file path for 9D model analysis by sympy
# OUTPUT_SP_9D_DIR_PATH: Path = Path(__file__).resolve().parent.parent / "output" / "9d" / "sp"
# CC_SP_9D_DIR_PATH: Path = OUTPUT_SP_9D_DIR_PATH / "cosmological_const"
# SUPPRESSED_CC_SP_9D_FILE_PATH: Path = CC_SP_9D_DIR_PATH / "suppressed_cc.json"
# FD_SP_9D_DIR_PATH: Path = OUTPUT_SP_9D_DIR_PATH / "first_derivative"
# CRITICAL_POINTS_SP_9D_FILE_PATH: Path = FD_SP_9D_DIR_PATH / "critical_points.json"
# SD_SP_9D_DIR_PATH: Path = OUTPUT_SP_9D_DIR_PATH / "second_derivative"
# MASSLESS_SOLUTION_SP_9D_DIR_PATH: Path = OUTPUT_SP_9D_DIR_PATH / "massless_solution"
# MINIMA_SP_9D_FILE_PATH: Path = SD_SP_9D_DIR_PATH / "minima.json"
# MAXIMA_SP_9D_FILE_PATH: Path = SD_SP_9D_DIR_PATH / "maxima.json"

# result file path for 9D model analysis by numpy
# OUTPUT_NP_9D_DIR_PATH: Path = Path(__file__).resolve().parent.parent / "output" / "9d" / "np"
# CC_NP_9D_DIR_PATH: Path = OUTPUT_NP_9D_DIR_PATH / "cosmological_const"
# SUPPRESSED_CC_NP_9D_FILE_PATH: Path = CC_NP_9D_DIR_PATH / "suppressed_cc.json"
# FD_NP_9D_DIR_PATH: Path = OUTPUT_NP_9D_DIR_PATH / "first_derivative"
# CRITICAL_POINTS_NP_9D_FILE_PATH: Path = FD_NP_9D_DIR_PATH / "critical_points.json"
# SD_NP_9D_DIR_PATH: Path = OUTPUT_NP_9D_DIR_PATH / "second_derivative"
# MASSLESS_SOLUTION_NP_9D_DIR_PATH: Path = OUTPUT_NP_9D_DIR_PATH / "massless_solution"
# MINIMA_NP_9D_FILE_PATH: Path = SD_NP_9D_DIR_PATH / "minima.json"
# MAXIMA_NP_9D_FILE_PATH: Path = SD_NP_9D_DIR_PATH / "maxima.json"
# result file path for 8D model analysis by numpy
# OUTPUT_NP_8D_DIR_PATH: Path = Path(__file__).resolve().parent.parent / "output" / "sp" / "8d"
# WL_NP_8D_DIR_PATH: Path = OUTPUT_NP_8D_DIR_PATH / "wilson_line"
# CC_NP_8D_DIR_PATH: Path = OUTPUT_NP_8D_DIR_PATH / "cosmological_const"
# SUPPRESSED_CC_NP_8D_FILE_PATH: Path = CC_NP_8D_DIR_PATH / "suppressed_cc.json"
