# StabilityAnalysis

Program to study stability of non-supersymmetric heterotic strings.

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

Create tables:

```bash
python analysis/sqlite/create_table.py
```

Insert master data:

```bash
python analysis/sqlite/insert_master_data.py
```

---

## How to run

### 9D analysis

1. Solve the massless conditions in the 9D supersymmetric model and insert results into `massless_solution_9d`:

   ```bash
   python analysis/analysis_9d/jobs/run_massless_solution.py
   ```

### 8D analysis

**Prerequisites**

- `moduli_9d` rows must already exist in the database.

**Steps**

1. **Moduli (8D)** — enumerate moduli candidates and insert into `moduli_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_moduli.py
   ```

2. **Cosmological constant** — compute for each modulus; results go into the `cosmological_constant` column of `moduli_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_cosmological_constant.py
   ```

3. **Critical points** — first derivative of the potential; results go into `is_critical_point` on `moduli_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_critical_point.py
   ```

4. **Hessian** — second derivative at each critical point; results go into `hessian` and `type` on `moduli_8d`:

   ```bash
   python analysis/analysis_8d/jobs/run_hessian.py
   ```
