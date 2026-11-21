"""Auto-drafted Suspicious Transaction Report (STR-style) for analyst review.

Template-based (no LLM), so it runs offline and is fully reproducible. The draft is built only
from the evidence bundle, public merchant fields and current-window features. It never reads
ground truth. It describes *purpose drift*; it does not claim any specific crime was detected.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

DISCLAIMER = ("DRAFT for analyst review. Not filed automatically. Signals, not proof: "
              "a human analyst decides whether to file.")


def _pct(x: Any) -> str:
    return "n/a" if x is None or pd.isna(x) else f"{float(x):.0%}"


def _ids(x: Any) -> str:
    """Hashed identifiers as a short comma list (raw values are never shown)."""
    if x is None:
        return "n/a"
    if isinstance(x, (list, tuple, np.ndarray)):
        return ", ".join(str(v) for v in x) or "n/a"
    return str(x)


def str_draft(ev: dict[str, Any], merchant: pd.Series, feats: pd.Series, cfg: dict[str, Any]) -> str:
    """Markdown STR-style draft for one merchant.

    `merchant` must be a public merchant row (no `label` / `archetype`); `feats` is the merchant's
    row from `features_current`; `ev` is its evidence bundle (optionally with a `claim`).
    """
    as_of = cfg["sim"]["end_date"]
    win = cfg["features"]["window_long"]
    pts = " / ".join(str(p) for p in cfg["features"]["price_points"])
    onboard = merchant.get("onboard_date")
    onboard = pd.Timestamp(onboard).strftime("%d %b %Y") if onboard is not None and not pd.isna(onboard) else "n/a"

    L = [f"# DRAFT STR: {ev['name']} ({ev['merchant_id']})", "",
         f"> {DISCLAIMER}", "",
         "**Reporting entity:** [Payment aggregator name] (demo)  ",
         f"**Report date (data as of):** {as_of}  ",
         "**Nature of concern:** Purpose drift. The merchant's payment behaviour does not fit its declared business.", "",
         "## 1. Subject",
         f"- Merchant: {ev['name']} ({ev['merchant_id']})",
         f"- Declared business: {str(ev['declared_category']).replace('_', ' ')}; city: {ev['city']}; onboarded: {onboard}",
         f"- Device IDs (hashed): {_ids(merchant.get('device_ids'))}",
         f"- Settlement bank account (hashed): {_ids(merchant.get('bank_account_hash'))}",
         f"- GSTIN (hashed): {_ids(merchant.get('gstin_hash'))}",
         "",
         f"## 2. Transaction summary (last {win} days)",
         f"- Payments: {int(feats['cnt_long']):,}; value: INR {float(feats['gmv_long']):,.0f}",
         f"- Share at exactly INR {pts}: {_pct(feats.get('pricepoint_share'))}",
         f"- Share between midnight and 5 am: {_pct(feats.get('night_share'))}",
         f"- Payers from outside {ev['city']}: {_pct(feats.get('nonlocal_share'))}",
         f"- Payments from repeat payers: {_pct(feats.get('repeat_txn_share'))}",
         f"- Payouts settled within 12 hours: {_pct(feats.get('fast_payout_share'))}",
         "",
         f"## 3. Grounds for suspicion (risk score {ev['risk_score']:.0f} / 100, {ev['tier']})"]
    L += [f"- {e}" for e in ev.get("evidence") or ["No single signal is far from peers."]]
    raising = [d["label"] for d in ev.get("drivers", []) if d["contribution"] > 0]
    if raising:
        L.append(f"- Main model drivers: {'; '.join(raising)}.")

    inn = ev["innocence"]
    L += ["", "## 4. Legitimate explanations considered",
          f"- Innocence Engine: **{inn['status']}**",
          f"- {inn['volume_text']}", f"- {inn['composition_text']}"]
    claim = ev.get("claim")
    if claim:
        L.append(f"- Merchant's own explanation: \"{claim['reason']}\". {claim['summary']}")
        L += [f"  - {'PASS' if k['passed'] else 'FAIL'}: {k['check']}" for k in claim["checks"]]
    else:
        L.append("- Merchant's own explanation: not yet requested.")

    L += ["", "## 5. Linked entities"] + [f"- {n.replace(' (Jaccard)', '')}" for n in ev.get("network") or ["No notable links."]]
    L += ["", "## 6. Recommended action",
          f"- {ev['rung']} (chosen by expected cost; see the investigation report)", "",
          "## 7. Analyst decision",
          "- [ ] File STR   - [ ] Do not file   - [ ] Need more information",
          "- Analyst name: ____________________   Date: ____________", "",
          f"> {DISCLAIMER}"]
    return "\n".join(L) + "\n"
