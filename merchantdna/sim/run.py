"""Run the simulator: `python -m merchantdna.sim.run [--small]` writes data/*.parquet."""
from __future__ import annotations

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from merchantdna.sim.calendar import build_calendar  # noqa: E402
from merchantdna.sim.merchants import build_merchants  # noqa: E402
from merchantdna.sim.profiles import hash_ids  # noqa: E402
from merchantdna.sim.transactions import (generate_merchant, make_pools,  # noqa: E402
                                          payer_city_index, settlements_for)
from merchantdna.utils.config import load_config, path_for  # noqa: E402
from merchantdna.utils.io import write_table  # noqa: E402
from merchantdna.utils.logging import Timer, get_logger  # noqa: E402

log = get_logger("sim")


def simulate(small: bool = False) -> dict[str, pd.DataFrame]:
    """Generate all tables in memory. Deterministic for a given config seed."""
    cfg = load_config()
    scale = cfg["sim"]["small" if small else "full"]
    n, n_days = scale["n_merchants"], scale["n_days"]
    rng = np.random.default_rng(cfg["seed"])

    cal = build_calendar(cfg, n_days, rng)
    merchants, plans = build_merchants(cfg, n, n_days, rng)
    n_rings = max(p["ring_id"] for p in plans) + 1
    pools = make_pools(cfg, n_rings, rng)

    parts = [generate_merchant(p, cal, cfg, pools, rng) for p in plans]
    tx = pd.concat(parts, ignore_index=True).sort_values("timestamp", kind="stable")
    settlements = settlements_for(tx, plans, cfg, rng)

    city_names = np.array([c[0] for c in cfg["sim"]["cities"]])
    tx = pd.DataFrame({
        "txn_id": np.arange(len(tx), dtype=np.int64),
        "merchant_id": pd.Categorical(tx["merchant_id"], categories=merchants["merchant_id"]),
        "payer_id_hash": hash_ids(tx["payer_raw"].to_numpy()),
        "timestamp": tx["timestamp"].to_numpy(),
        "amount": tx["amount"].to_numpy(),
        "channel": pd.Categorical(np.where(tx["is_card"], "card", "UPI")),
        "payer_city": pd.Categorical(city_names[payer_city_index(tx["payer_raw"].to_numpy(), pools)]),
        "is_refund": tx["is_refund"].to_numpy(),
    })
    calendar = cal.assign(match_start=pd.to_datetime(cal["match_start"]))
    return {"merchants": merchants, "transactions": tx, "settlements": settlements, "calendar": calendar}


def sanity_plots(tables: dict[str, pd.DataFrame]) -> None:
    """Quick visual checks written to reports/sim/."""
    out = path_for("reports") / "sim"
    out.mkdir(parents=True, exist_ok=True)
    tx = tables["transactions"].merge(tables["merchants"][["merchant_id", "archetype"]], on="merchant_id")
    tx["hour"] = tx["timestamp"].dt.hour

    prof = tx.groupby(["archetype", "hour"]).size().unstack(fill_value=0)
    (prof.div(prof.sum(axis=1), axis=0).T).plot(figsize=(11, 5), title="Hourly profile by archetype")
    plt.ylabel("share of txns"); plt.tight_layout(); plt.savefig(out / "hourly_by_archetype.png"); plt.close()

    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    for ax, arch in zip(axes.ravel(), ["normal", "festival_surge", "betting_collector",
                                       "slow_drift", "mule_network", "adaptive_mimic"]):
        a = tx.loc[(tx["archetype"] == arch) & (tx["amount"] < 3000), "amount"]
        ax.hist(a, bins=120); ax.set_title(arch)
    fig.suptitle("Amount histograms (< INR 3000)"); fig.tight_layout()
    fig.savefig(out / "amount_hist_by_archetype.png"); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
    for mid, name in [("M0000", "SweetCrust"), ("M0001", "FreshOven")]:
        t = tx[tx["merchant_id"] == mid]
        t.groupby(t["timestamp"].dt.normalize()).size().plot(ax=axes[0], label=name)
        h = t.groupby("hour").size().reindex(range(24), fill_value=0)
        axes[1].plot(h.index, h / h.sum(), label=name, marker="o")
    axes[0].set_title("Daily transactions"); axes[1].set_title("Hourly share (whole period)")
    for ax in axes:
        ax.legend()
    fig.tight_layout(); fig.savefig(out / "sweetcrust_vs_freshoven.png"); plt.close(fig)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", action="store_true", help="120 merchants x 60 days for development")
    args = ap.parse_args()
    with Timer(log, "simulation"):
        tables = simulate(args.small)
    for name, df in tables.items():
        write_table(df, name)
        log.info("%-12s %9d rows", name, len(df))
    log.info("archetype mix:\n%s", tables["merchants"]["archetype"].value_counts().to_string())
    sanity_plots(tables)


if __name__ == "__main__":
    main()
