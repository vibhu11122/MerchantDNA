"""Cached loaders. The app only READS artefacts; it never trains or recomputes on page load."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merchantdna.utils.config import load_config  # noqa: E402
from merchantdna.utils.io import load_artifact, read_json, read_table  # noqa: E402


@st.cache_data(show_spinner=False)
def config() -> dict:
    return load_config()


@st.cache_data(show_spinner=False)
def scores() -> pd.DataFrame:
    return read_table("scores", "artifacts").set_index("merchant_id")


@st.cache_data(show_spinner=False)
def evidence() -> dict:
    return read_json("evidence", "artifacts")


@st.cache_data(show_spinner=False)
def metrics() -> dict:
    return read_json("metrics")


@st.cache_data(show_spinner=False)
def table(name: str) -> pd.DataFrame:
    """Any artefact table (features_current, dna_trajectory, volume_bands, daily_counts...)."""
    return read_table(name, "artifacts")


@st.cache_data(show_spinner=False)
def calendar() -> pd.DataFrame:
    return read_table("calendar")


@st.cache_data(show_spinner=False)
def merchants_public() -> pd.DataFrame:
    """Merchant table without ground truth (the app never shows labels)."""
    return read_table("merchants").drop(columns=["label", "archetype"]).set_index("merchant_id")


@st.cache_resource(show_spinner=False)
def artifact(name: str):
    """Large Python objects (model bundle, cohort stats, hour x day cube)."""
    return load_artifact(name)


@st.cache_data(show_spinner=False)
def merchant_txns(mid: str) -> pd.DataFrame:
    return read_table("transactions", filters=[("merchant_id", "==", mid)])


@st.cache_data(show_spinner=False)
def merchant_settlements(mid: str) -> pd.DataFrame:
    return read_table("settlements", filters=[("merchant_id", "==", mid)])


def artefacts_ready() -> bool:
    return (ROOT / "artifacts" / "scores.parquet").exists() and (ROOT / "reports" / "metrics.json").exists()
