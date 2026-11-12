"""Small helpers to read and write Parquet tables and joblib artefacts."""
from __future__ import annotations

import json
from typing import Any

import joblib
import pandas as pd

from merchantdna.utils.config import path_for

LABEL_COLUMNS = ("label", "archetype")  # ground truth: evaluation only, never model input


def write_table(df: pd.DataFrame, name: str, kind: str = "data") -> None:
    """Save a DataFrame as <kind>/<name>.parquet."""
    df.to_parquet(path_for(kind) / f"{name}.parquet", index=False)


def read_table(name: str, kind: str = "data", columns: list[str] | None = None,
               filters: list | None = None) -> pd.DataFrame:
    """Load <kind>/<name>.parquet, optionally only some columns or rows."""
    return pd.read_parquet(path_for(kind) / f"{name}.parquet", columns=columns, filters=filters)


def read_merchants_for_models() -> pd.DataFrame:
    """Merchant table WITHOUT ground-truth columns. Every model must use this."""
    return read_table("merchants").drop(columns=list(LABEL_COLUMNS))


def save_artifact(obj: Any, name: str) -> None:
    """Persist any Python object to artifacts/<name>.joblib."""
    joblib.dump(obj, path_for("artifacts") / f"{name}.joblib")


def load_artifact(name: str) -> Any:
    """Load artifacts/<name>.joblib."""
    return joblib.load(path_for("artifacts") / f"{name}.joblib")


def write_json(obj: Any, name: str, kind: str = "reports") -> None:
    """Write a JSON file (pretty-printed) to <kind>/<name>.json."""
    with open(path_for(kind) / f"{name}.json", "w") as f:
        json.dump(obj, f, indent=2, default=float)


def read_json(name: str, kind: str = "reports") -> Any:
    """Read <kind>/<name>.json."""
    with open(path_for(kind) / f"{name}.json") as f:
        return json.load(f)
