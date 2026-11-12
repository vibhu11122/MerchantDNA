"""Load config.yaml once and expose it as a plain dict."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_config(path: str | None = None) -> dict[str, Any]:
    """Read the YAML config (cached) and return it as a dict."""
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def path_for(kind: str) -> Path:
    """Absolute path of a data / artifacts / reports folder, created if missing."""
    p = ROOT / load_config()["paths"][kind]
    p.mkdir(parents=True, exist_ok=True)
    return p
