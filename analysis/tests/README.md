# Mathematica reference validation (pytest)

Compare SQLite `moduli_8d` results with Mathematica CSV exports under `output/`.

## Prerequisites

- `.env` with `DATABASE_PATH` pointing at your populated DB
- Reference CSV files:
  - `output/moduli_8d_cosmological_const.csv`
  - `output/moduli_8d_critical_point.csv`
  - `output/moduli_8d_hessian.csv`

## Run

From the repository root:

```bash
pip install -r requirements.txt
pytest analysis/tests -v
```

## Partial DB

By default, only Mathematica `moduli_9d_id` values whose **parent** `removed_nodes` exist in DB `moduli_9d` are compared.

Optional environment variables:

| Variable | Description |
|----------|-------------|
| `REFERENCE_MODULI_9D_IDS` | Comma-separated Mathematica ids, e.g. `1,3` |
| `REFERENCE_PARENT_REMOVED_NODES` | Pipe-separated canonical parent JSON strings |
| `REFERENCE_MIN_MATCHED_ROWS` | Minimum matched rows (default `1`) |
| `REFERENCE_MIN_MATCH_RATIO` | Minimum matched/csv ratio (default `0`) |

Example:

```bash
REFERENCE_MODULI_9D_IDS=1,3 pytest analysis/tests -v
```
