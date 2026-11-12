"""Hero merchants must reach their expected tiers through the models alone."""
from __future__ import annotations

import pandas as pd
import pytest

from merchantdna.utils.config import ROOT
from merchantdna.utils.io import read_json

SCORES = ROOT / "artifacts" / "scores.parquet"
EXPECTED = {"M0000": "LOW", "M0001": "HIGH", "M0002": "MEDIUM"}

pytestmark = pytest.mark.skipif(not SCORES.exists(), reason="run `make all` first")


@pytest.fixture(scope="module")
def scores() -> pd.DataFrame:
    return pd.read_parquet(SCORES).set_index("merchant_id")


@pytest.mark.parametrize("mid,tier", EXPECTED.items())
def test_hero_tier(scores, mid, tier):
    assert scores.loc[mid, "tier"] == tier, f"{mid} scored {scores.loc[mid, 'risk_score']:.1f}"


def test_heroes_never_in_training_labels(scores):
    labelled = set(read_json("labelled_set", "artifacts")["labelled"])
    assert not labelled & set(EXPECTED)


def test_sweetcrust_cleared_by_innocence_engine(scores):
    assert scores.loc["M0000", "innocence_status"] == "Cleared"
    assert bool(scores.loc["M0000", "volume_up"])


def test_freshoven_not_discounted(scores):
    """Composition shifts must never be discounted by the Innocence Engine."""
    assert scores.loc["M0001", "innocence_status"].startswith("Not cleared")


def test_quickkart_is_investigated_not_suspended(scores):
    assert scores.loc["M0002", "rung"].startswith("Soft step-up")


def test_scores_are_not_hardcoded():
    """No source file outside the simulator / tests mentions a hero's score or tier."""
    for path in (ROOT / "merchantdna").rglob("*.py"):
        if "sim" in path.parts:
            continue
        text = path.read_text()
        for mid in EXPECTED:
            for line in text.splitlines():
                if mid in line:
                    assert "HEROES" in line or "exclude" in line or line.strip().startswith("#"), (path, line)
