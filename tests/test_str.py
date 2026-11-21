"""The auto-drafted STR: produced for every hero, grounded in evidence, never leaks ground truth."""
from __future__ import annotations

from pathlib import Path

import pytest

from merchantdna.decision.str_report import str_draft
from merchantdna.utils.config import load_config
from merchantdna.utils.io import read_json, read_table

ROOT = Path(__file__).resolve().parents[1]
HEROES = ["M0000", "M0001", "M0002"]

pytestmark = pytest.mark.skipif(not (ROOT / "artifacts" / "scores.parquet").exists(), reason="run `make all` first")


@pytest.fixture(scope="module")
def inputs():
    merchants = read_table("merchants").drop(columns=["label", "archetype"]).set_index("merchant_id")
    feats = read_table("features_current", "artifacts").set_index("merchant_id")
    return read_json("evidence", "artifacts"), merchants, feats, load_config()


def _draft(inputs, mid: str, claim: str | None = None) -> str:
    ev, merchants, feats, cfg = inputs
    e = dict(ev[mid])
    if claim:
        e["claim"] = e["claims"][claim]
    return str_draft(e, merchants.loc[mid], feats.loc[mid], cfg)


@pytest.mark.parametrize("mid", HEROES)
def test_str_for_every_hero(inputs, mid):
    text = _draft(inputs, mid)
    assert inputs[0][mid]["name"] in text and "DRAFT" in text and "Analyst decision" in text


def test_freshoven_str_contains_evidence(inputs):
    text = _draft(inputs, "M0001", claim="festival")
    for line in inputs[0]["M0001"]["evidence"]:
        assert line in text
    assert "Merchant's own explanation" in text


@pytest.mark.parametrize("mid", HEROES)
def test_str_has_no_ground_truth_or_overclaim(inputs, mid):
    text = _draft(inputs, mid).lower()
    for word in ("label", "archetype", "betting detected"):
        assert word not in text
