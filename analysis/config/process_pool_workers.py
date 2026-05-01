"""Helpers shared by parallel analysis jobs using ``ProcessPoolExecutor``."""

from __future__ import annotations

import os


def max_workers_from_env(env_var_name: str) -> int:
    """
    Process count from ``env_var_name`` when set to a positive integer,
    otherwise ``max(1, cpu_count - 1)``.
    """
    raw = os.getenv(env_var_name, "").strip()
    if raw:
        return max(1, int(raw, 10))
    n = os.cpu_count() or 1
    return max(1, n - 1)
