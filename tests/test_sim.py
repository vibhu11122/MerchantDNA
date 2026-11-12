"""Simulator: archetype mix, hero merchants, schema, determinism."""
from __future__ import annotations

import pandas as pd

from merchantdna.sim.run import simulate
from merchantdna.utils.config import load_config

MERCHANT_COLS = {"merchant_id", "name", "declared_category", "city", "onboard_date", "has_website",
                 "website_text", "device_ids", "bank_account_hash", "ip_cluster", "address_hash",
                 "gstin_hash", "is_franchise", "label", "archetype"}
TXN_COLS = {"txn_id", "merchant_id", "payer_id_hash", "timestamp", "amount", "channel",
            "payer_city", "is_refund"}


def test_schema(small_sim):
    assert set(small_sim["merchants"].columns) == MERCHANT_COLS
    assert set(small_sim["transactions"].columns) == TXN_COLS
    assert {"merchant_id", "date", "payout_amount", "payout_delay_hours"} <= set(small_sim["settlements"].columns)
    assert {"date", "is_diwali_window", "ipl_match", "wicket_minutes"} <= set(small_sim["calendar"].columns)


def test_archetype_mix(small_sim):
    m = small_sim["merchants"]
    cfg = load_config()
    for arch in cfg["sim"]["fraud_archetypes"]:
        assert (m["archetype"] == arch).sum() >= 1, arch
    fraud_share = m["label"].mean()
    assert 0.03 <= fraud_share <= 0.12
    assert m["has_website"].between(0, 1).all()
    # Fraud and honest merchants have websites at similar rates (no free signal from absence)
    rates = m.groupby("label")["has_website"].mean()
    assert abs(rates[0] - rates[1]) < 0.35


def test_heroes_present(small_sim):
    m = small_sim["merchants"].set_index("merchant_id")
    assert m.loc["M0000", "name"] == "SweetCrust Bakery" and m.loc["M0000", "label"] == 0
    assert m.loc["M0001", "name"] == "FreshOven Bakery" and m.loc["M0001", "label"] == 1
    assert m.loc["M0002", "name"] == "QuickKart Store"


def test_quickkart_shares_device_with_ring(small_sim):
    m = small_sim["merchants"].set_index("merchant_id")
    qk_dev = m.loc["M0002", "device_ids"][0]
    sharers = m[m["device_ids"].apply(lambda d: qk_dev in list(d))]
    assert len(sharers) >= 2 and (sharers["archetype"] == "mule_network").all()


def test_deterministic():
    a = simulate(small=True)["transactions"]["amount"].head(1000)
    b = simulate(small=True)["transactions"]["amount"].head(1000)
    pd.testing.assert_series_equal(a, b)


def test_sweetcrust_diwali_spike(small_sim):
    tx, cal = small_sim["transactions"], small_sim["calendar"]
    t = tx[tx["merchant_id"] == "M0000"]
    daily = t.groupby(t["timestamp"].dt.normalize()).size()
    peak = cal.loc[cal["is_diwali_peak"], "date"]
    normal = cal.loc[~cal["is_diwali_window"], "date"]
    assert daily.reindex(peak).mean() > 5 * daily.reindex(normal).mean()
