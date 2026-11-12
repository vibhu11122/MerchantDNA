"""Shared fixtures: a small in-memory simulation (fast) and paths to built artefacts."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))      # streamlit run adds the app folder; tests must too


@pytest.fixture(scope="session")
def small_sim():
    """Tables from the --small simulator config, generated in memory (not written to disk)."""
    from merchantdna.sim.run import simulate
    return simulate(small=True)


def artifacts_ready() -> bool:
    """True once `make all` has produced scores."""
    return (ROOT / "artifacts" / "scores.parquet").exists()
