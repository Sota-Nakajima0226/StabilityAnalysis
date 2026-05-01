from __future__ import annotations

import os
from pathlib import Path

_DOTENV_LOADED = False
_REPO_ROOT = Path(__file__).parent.parent.parent


def ensure_dotenv_loaded() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    env_path = _REPO_ROOT / ".env"
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except ImportError:
        raise ImportError("dotenv is not installed")
    _DOTENV_LOADED = True


ensure_dotenv_loaded()


class EnvSettings:
    def __init__(self) -> None:
        raw_db = os.getenv("DATABASE_PATH", "").strip()
        if not raw_db:
            raise RuntimeError(
                "DATABASE_PATH must be set in the environment (e.g. in `.env`)."
            )
        p = Path(raw_db)
        self._database_path = str(
            p.resolve() if p.is_absolute() else (_REPO_ROOT / p).resolve()
        )

        self.app_config_yml_path = self._resolve_config_yml_path()

        self.analysis_8d_debug = self._truthy(os.getenv("ANALYSIS_8D_DEBUG"), False)
        self.analysis_9d_debug = self._truthy(os.getenv("ANALYSIS_9D_DEBUG"), False)

        self.analysis_8d_target_moduli_9d_ids = self._int_list(
            "ANALYSIS_8D_TARGET_MODULI_9D_IDS", [3]
        )
        self.analysis_8d_target_moduli_8d_ids = self._int_list(
            "ANALYSIS_8D_TARGET_MODULI_8D_IDS", [14]
        )
        self.analysis_9d_target_moduli_9d_ids = self._int_list(
            "ANALYSIS_9D_TARGET_MODULI_9D_IDS", [3]
        )

        self.analysis_8d_coset_chunk_size = self._int(
            "ANALYSIS_8D_COSET_CHUNK_SIZE", 5000
        )
        self.analysis_8d_cosmological_const_chunk_size = self._int(
            "ANALYSIS_8D_COSMOLOGICAL_CONST_CHUNK_SIZE", 5000
        )
        self.analysis_8d_critical_point_chunk_size = self._int(
            "ANALYSIS_8D_CRITICAL_POINT_CHUNK_SIZE", 5000
        )
        self.analysis_8d_hessian_chunk_size = self._int(
            "ANALYSIS_8D_HESSIAN_CHUNK_SIZE", 5000
        )
        self.analysis_8d_hessian_eigenvalue_round_digits = self._int(
            "ANALYSIS_8D_HESSIAN_EIGENVALUE_ROUND_DIGITS", 8
        )

    @property
    def database_path(self) -> str:
        return self._database_path

    def _resolve_config_yml_path(self) -> Path:
        raw = os.getenv("CONFIG_YML_PATH", "").strip()
        if raw:
            p = Path(raw)
            return p if p.is_absolute() else _REPO_ROOT / p
        return _REPO_ROOT / "config" / "config.yml"

    def _truthy(self, raw: str | None, default: bool) -> bool:
        if raw is None or not raw.strip():
            return default
        return raw.strip().lower() in ("1", "true", "yes", "on")

    def _int(self, name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None or not str(raw).strip():
            return default
        return int(str(raw).strip(), 10)

    def _int_list(self, name: str, default: list[int]) -> list[int]:
        if name not in os.environ:
            return list(default)
        raw = os.environ.get(name, "").strip()
        if raw == "":
            return []
        return [int(x.strip(), 10) for x in raw.split(",") if x.strip()]


ENV = EnvSettings()
