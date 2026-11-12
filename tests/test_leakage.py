"""No ground truth may reach model inputs."""
from __future__ import annotations

import pandas as pd
import pytest

from merchantdna.features import columns as C
from merchantdna.utils.config import ROOT
from merchantdna.utils.io import read_merchants_for_models


def test_model_merchant_view_has_no_labels():
    if not (ROOT / "data" / "merchants.parquet").exists():
        pytest.skip("run `make data` first")
    assert not (set(read_merchants_for_models().columns) & C.LABEL_LIKE)


def test_feature_store_has_no_labels():
    path = ROOT / "artifacts" / "features_current.parquet"
    if not path.exists():
        pytest.skip("run `make features` first")
    cols = set(pd.read_parquet(path).columns)
    assert not (cols & C.LABEL_LIKE)
    assert not any(c.endswith("is_bet") for c in cols)


def test_feature_groups_have_no_labels():
    for group in [C.SHAPE, C.PEER_Z, C.VOLUME, C.HISTORY_DELTA]:
        assert not (set(group) & C.LABEL_LIKE)
