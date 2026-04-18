"""
Application logging under the ``analysis`` logger namespace.

- Log level is controlled by environment variable `LOG_LEVEL`.
- Log file directory / format / per-component file path are controlled by YAML.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from config.env_settings import ensure_dotenv_loaded
from config.yaml_settings import YAML

_LOG_NAMESPACE = "analysis"
_CONFIGURED = False
_FORMAT_DEFAULT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DATEFMT_DEFAULT = "%Y-%m-%d %H:%M:%S"

_REPO_ROOT = Path(__file__).parent.parent.parent


def _analysis_section_and_script(component: str) -> tuple[str, str]:
    """Return (yaml_section, script_key), e.g. (\"analysis_8d\", \"moduli\")."""
    if component.endswith("_9d"):
        return "analysis_9d", component[: -len("_9d")]
    if component.endswith("_8d"):
        return "analysis_8d", component[: -len("_8d")]
    return "analysis_8d", component


def _resolve_log_path_for_component(component: str) -> Path | None:
    """
    Resolve log file path for `analysis.<component>`.
    """
    by_component = YAML.logging.component_file_paths
    candidate = by_component.get(component) if by_component else None
    if isinstance(candidate, str) and candidate.strip():
        return _resolve_relative_log_path(candidate)

    section, script_name = _analysis_section_and_script(component)
    if section == "analysis_8d":
        raw = YAML.analysis_8d.log_file_path(script_name)
    else:
        raw = YAML.analysis_9d.log_file_path(script_name)
    if isinstance(raw, str) and raw.strip():
        return _resolve_relative_log_path(raw)

    fallback = YAML.logging.file_path
    if isinstance(fallback, str) and fallback.strip():
        return _resolve_relative_log_path(fallback)
    return None


def _resolve_relative_log_path(raw: str) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    log_dir = YAML.logging.directory
    if isinstance(log_dir, str) and log_dir.strip() and len(p.parts) == 1:
        return _REPO_ROOT / log_dir / p
    return _REPO_ROOT / p


def configure_logging(force: bool = False) -> None:
    global _CONFIGURED
    if _CONFIGURED and not force:
        return
    ensure_dotenv_loaded()
    level_name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = YAML.logging.format
    if not isinstance(fmt, str) or not fmt.strip():
        fmt = _FORMAT_DEFAULT
    datefmt = YAML.logging.datefmt
    if not isinstance(datefmt, str) or not datefmt.strip():
        datefmt = _DATEFMT_DEFAULT

    pkg = logging.getLogger(_LOG_NAMESPACE)
    if force:
        pkg.handlers.clear()
    if not pkg.handlers:
        formatter = logging.Formatter(
            fmt,
            datefmt=datefmt,
        )
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        pkg.addHandler(stderr_handler)
    pkg.setLevel(level)
    pkg.propagate = False
    _CONFIGURED = True


def get_logger(component: str) -> logging.Logger:
    """
    Return a logger named ``analysis.<component>`` (e.g. ``component='moduli_8d'``).
    """
    configure_logging()
    logger = logging.getLogger(f"{_LOG_NAMESPACE}.{component}")
    file_path = _resolve_log_path_for_component(component)
    if file_path is not None:
        existing = any(
            isinstance(h, logging.FileHandler) and Path(h.baseFilename) == file_path
            for h in logger.handlers
        )
        if not existing:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            fmt = YAML.logging.format
            if not isinstance(fmt, str) or not fmt.strip():
                fmt = _FORMAT_DEFAULT
            datefmt = YAML.logging.datefmt
            if not isinstance(datefmt, str) or not datefmt.strip():
                datefmt = _DATEFMT_DEFAULT
            formatter = logging.Formatter(str(fmt), datefmt=str(datefmt))
            fh = logging.FileHandler(file_path, encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger
