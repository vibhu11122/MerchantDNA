"""Merchant "Explain" step: before any hold, the merchant can give a reason; we test it.

A claim is accepted only if the data agree with it. For example "festival" is accepted
only if peers in the same window also spiked AND the business mix is unchanged.
"""
from __future__ import annotations

from typing import Any

REASONS = ["festival", "new branch", "promotion", "bulk order", "other"]


def _check(text: str, ok: bool) -> dict[str, Any]:
    return {"check": text, "passed": bool(ok)}


def verify_claim(reason: str, ev: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    """Test one claimed reason against a merchant's evidence (innocence + features)."""
    p = cfg["models"]["innocence"]
    shifted = set(ev["shifted"])
    if reason == "festival":
        checks = [
            _check(f"Peers in the same category and city tier also spiked "
                   f"(up to x{ev['peer_uplift_hi_max']:.1f})", ev["peer_uplift_hi_max"] >= p["min_peer_uplift_festival"]),
            _check("Extra volume stays inside the expected range", ev["volume_explained"]),
            _check("Trading hours unchanged", "hours" not in shifted),
            _check("Amount mix unchanged", "amounts" not in shifted),
            _check("Payer geography unchanged", "payers" not in shifted),
        ]
    elif reason == "new branch":
        checks = [
            _check("Trading hours unchanged", "hours" not in shifted),
            _check("Amount mix unchanged", "amounts" not in shifted),
            _check("New payers are not spread across many cities",
                   ev["z_multi_city_payer_share"] < p["composition_z"]),
        ]
    elif reason == "promotion":
        checks = [
            _check("Trading hours unchanged", "hours" not in shifted),
            _check("Payer geography unchanged", "payers" not in shifted),
            _check("Typical ticket did not rise", ev["d_amt_median"] <= 0.1 * max(ev["amt_median"], 1)),
            _check("No clustering on fixed price points", ev["z_pricepoint_share"] < p["composition_z"]),
        ]
    elif reason == "bulk order":
        checks = [
            _check("Value grew much more than the number of payments",
                   ev["ticket_growth"] > 2 and ev["growth_short_vs_long"] < 1.5),
            _check("Trading hours unchanged", "hours" not in shifted),
            _check("Payer geography unchanged", "payers" not in shifted),
        ]
    else:
        checks = [_check("Free-text reason: needs an analyst to verify", False)]
    accepted = all(c["passed"] for c in checks)
    return {"reason": reason, "accepted": accepted, "checks": checks,
            "summary": ("Claim is consistent with the data." if accepted
                        else "Claim is NOT supported by the data; failed checks are listed.")}


def verify_all(ev: dict[str, Any], cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Result of every possible claim, so the report and app can show any choice instantly."""
    return {r: verify_claim(r, ev, cfg) for r in REASONS}
