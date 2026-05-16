# StabilityAnalysis

Program to study stability of non-supersymmetric heterotic strings.

---

## Python and dependencies

### Python

Developed and tested with a conda environment (**Python 3.13** in the reference setup):

```bash
conda create -n <your-env> Python=3.13
conda activate <your-env>
```

### Computation library

Physical calculations in this project are performed with **[SymPy](https://www.sympy.org/)** (1.14.0): vectors and matrices, exact rationals, root generation, massless conditions, coset classification, derivatives, and Hessian eigenvalue analysis.

### Other dependencies

| Library | Version | Role |
|---------|---------|------|
| [PyYAML](https://pyyaml.org/) | 6.0.2 | `config/config.yml` |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 1.0.1 | `.env` loading |

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration

### Environment (`.env`)

On import, `analysis/config/env_settings.py` loads `.env` **once** and exposes settings on the global **`ENV`** object (for example `ENV.database_path`, `ENV.analysis_8d_debug`, **`ENV.app_config_yml_path`**). **`DATABASE_PATH` is required.**

### YAML (`config/config.yml` by default)

The path comes from **`ENV.app_config_yml_path`**. `analysis/config/yaml_settings.py` reads that file **once** and exposes the global **`YAML`** object (for example `YAML.paths.input_dir`, `YAML.logging.directory`, `YAML.analysis_8d.log_file_path("moduli")`). For backward compatibility, `get_config`, `get_config_path`, and `get_config_value` are provided from the same module.

### Other notes

| Item | Description |
|------|-------------|
| `LOG_LEVEL` | Environment variable for console log verbosity. |
| YAML overrides | Any leaf in YAML can be overridden by an env var: dotted path → `UPPER_SNAKE` (e.g. `paths.input_dir` → `PATHS_INPUT_DIR`). |

### Logging (file output)

Configured in YAML:

- `logging.directory`, `logging.format`, `logging.datefmt`
- Per script: `analysis_8d.<script>.log_file_path` or `analysis_9d.<script>.log_file_path`

---

## Preparation

Before running the preparation script:

1. Create and edit `.env`:

   ```bash
   cp .env.example .env
   ```

   Set `DATABASE_PATH` in `.env` to your SQLite DB path.

2. Create the DB file (example):

   ```bash
   sqlite3 ./db/stability_analysis.db ".databases"
   ```

Run all preparation steps at once:

```bash
./script/setup_preparation.sh
```

Or run each step manually.

Create tables:

```bash
python analysis/sqlite/create_table.py
```

`create_table.py` also creates an index on `coset_8d (moduli_8d_id, character)` to speed up the cosmological-constant aggregation.

Insert master data:

```bash
python analysis/sqlite/insert_master_data.py
```

---

## How to run

### 9D analysis

1. **Cosmological constant** — compute for each modulus; results go into the `cosmological_constant` column of `moduli_9d` with `use_analysis_9d=true`:

   ```bash
   python analysis/analysis_9d/jobs/run_cosmological_constant.py
   ```

2. **Critical points** — compute for each modulus; results go into the `is_critical_point` column of `moduli_9d` with `use_analysis_9d=true`:

   ```bash
   python analysis/analysis_9d/jobs/run_critical_point.py
   ```

3. **Hessian** — second derivative at each critical point; results go into `hessian` and `type` on `moduli_9d` with `use_analysis_9d=true`:

   ```bash
   python analysis/analysis_9d/jobs/run_hessian.py
   ```


### 8D analysis

**Prerequisites**

- Solve the massless conditions in the 9D supersymmetric model and insert results into `massless_solution_9d`:

   ```bash
   python analysis/analysis_9d/jobs/run_massless_solution.py
   ```

**Steps**

1. **Moduli (8D)** — enumerate moduli candidates and insert into `moduli_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_moduli.py
   ```

2. **Coset (8D)** — classify the massless solutions by the inner products with the moduli and insert into `coset_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_coset.py
   ```

3. **Cosmological constant** — compute for each modulus; results go into the `cosmological_constant` column of `moduli_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_cosmological_constant.py
   ```

4. **Critical points** — first derivative of the potential; results go into `is_critical_point` on `moduli_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_critical_point.py
   ```

5. **Hessian** — second derivative at each critical point; results go into `hessian` and `type` on `moduli_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_hessian.py
   ```
