from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from config.env_settings import ENV

_CONFIG_CACHE: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    def _load_yaml_file(path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            return {}
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {}

    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = _load_yaml_file(ENV.app_config_yml_path)
    return _CONFIG_CACHE


class YamlPathSettings:
    """``paths.*`` from YAML."""

    def __init__(self, root: YamlSettings):
        self._y = root

    @property
    def input_dir(self) -> Path:
        return self._y._resolve_repo_path("paths.input_dir", "input")

    @property
    def output_8d_dir(self) -> Path:
        return self._y._resolve_repo_path("paths.output_8d_dir", "output/8d")

    @property
    def output_9d_dir(self) -> Path:
        return self._y._resolve_repo_path("paths.output_9d_dir", "output/9d")


class YamlLoggingSettings:
    """``logging.*`` from YAML."""

    def __init__(self, root: YamlSettings):
        self._y = root

    @property
    def directory(self) -> str:
        return self._y._get_str("logging.directory", "logs")

    @property
    def format(self) -> str:
        v = self._y._get("logging.format", "")
        return str(v) if v else ""

    @property
    def datefmt(self) -> str:
        v = self._y._get("logging.datefmt", "")
        return str(v) if v else ""

    @property
    def file_path(self) -> str:
        return self._y._get_str("logging.file_path", "logs/stability_analysis.log")

    @property
    def component_file_paths(self) -> dict[str, Any]:
        v = self._y._get("logging.component_file_paths", {})
        return v if isinstance(v, dict) else {}


class YamlAnalysisSection:
    """``analysis_8d.<script>.*`` or ``analysis_9d.<script>.*``."""

    def __init__(self, root: YamlSettings, prefix: str):
        self._y = root
        self._prefix = prefix

    def log_file_path(self, script: str) -> str:
        v = self._y._get(f"{self._prefix}.{script}.log_file_path", "")
        return str(v).strip() if v else ""


class YamlSettings:
    """Root accessor; sub-objects group related YAML keys."""

    def __init__(self) -> None:
        self.paths = YamlPathSettings(self)
        self.logging = YamlLoggingSettings(self)
        self.analysis_8d = YamlAnalysisSection(self, "analysis_8d")
        self.analysis_9d = YamlAnalysisSection(self, "analysis_9d")

    def _get(self, path: str, default: Any = None) -> Any:
        current: Any = get_config()
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    def _get_str(self, path: str, default: str) -> str:
        env_key = path.replace(".", "_").upper()
        raw = os.getenv(env_key)
        if raw is not None and raw.strip() != "":
            return raw.strip()
        v = self._get(path, default)
        return str(v) if v is not None else default

    def _resolve_repo_path(self, path: str, default_relative: str) -> Path:
        raw = self._get_str(path, default_relative)
        p = Path(raw)
        if p.is_absolute():
            return p
        return Path(__file__).parent.parent.parent / p


YAML = YamlSettings()
