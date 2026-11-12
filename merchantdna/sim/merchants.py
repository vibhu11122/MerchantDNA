"""Build the merchant table and the hidden per-merchant simulation parameters."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from merchantdna.sim.heroes import HEROES

NAME_PREFIX = ["Sri", "New", "Royal", "Golden", "Happy", "City", "Star", "Green", "Super",
               "Annapurna", "Lakshmi", "Krishna", "Metro", "Daily", "Fresh", "Prime", "Om"]
CATEGORY_NOUN = {"bakery": "Bakery", "grocery": "Kirana Store", "restaurant": "Restaurant",
                 "electronics": "Electronics", "pharmacy": "Medicals", "gym_or_tuition": "Fitness & Tuition"}
VOCAB = {
    "bakery": "fresh bread cakes pastries cookies birthday cake custom orders eggless baked daily "
              "croissant muffins sweets buns rusk cream celebration bakery oven",
    "grocery": "groceries rice dal atta oil vegetables fruits daily needs home delivery kirana "
               "household staples spices snacks dairy milk",
    "restaurant": "menu biryani thali dine in takeaway family restaurant veg non veg tandoor "
                  "lunch dinner chef dishes table booking",
    "electronics": "mobiles laptops televisions appliances warranty emi offers accessories "
                   "chargers headphones service centre brands exchange",
    "pharmacy": "medicines prescription pharmacy healthcare generic drugs wellness chemist "
                "home delivery tablets syrups first aid",
    "gym_or_tuition": "fitness training classes coaching batch membership personal trainer "
                      "tuition maths science exam preparation students monthly fees",
}
GENERIC = "welcome quality best service order online visit contact us trusted since years customers"
GAMING = "win cash prizes daily contest fantasy league rewards instant withdrawal bonus play now " \
         "refer earn jackpot prediction match odds wallet"


def _hex(rng: np.random.Generator, prefix: str) -> str:
    """Random opaque identifier like 'dev_3fa9c1d2e4b5a697'."""
    return f"{prefix}_{rng.integers(0, 2**63):016x}"


def website_text(rng: np.random.Generator, category: str, style: str, n_words: int = 30) -> str:
    """Generate a website blurb: clean category text, generic text, or text leaking gaming words."""
    cat_words, gen_words, game_words = VOCAB[category].split(), GENERIC.split(), GAMING.split()
    if style == "gaming":
        pools, probs = [cat_words, gen_words, game_words], [0.35, 0.25, 0.40]
    elif style == "generic":
        pools, probs = [cat_words, gen_words], [0.25, 0.75]
    else:
        pools, probs = [cat_words, gen_words], [0.75, 0.25]
    picks = rng.choice(len(pools), size=n_words, p=probs)
    return " ".join(pools[i][rng.integers(len(pools[i]))] for i in picks)


def _archetype_list(cfg: dict[str, Any], n: int, rng: np.random.Generator) -> list[str]:
    """Exact archetype counts for n merchants; each fraud type appears at least once (mules >= 3)."""
    shares = cfg["sim"]["archetypes"]
    counts = {a: int(round(s * n)) for a, s in shares.items()}
    for a in cfg["sim"]["fraud_archetypes"]:
        counts[a] = max(counts[a], 3 if a == "mule_network" else 1)
    counts["normal"] += n - sum(counts.values())
    arch = [a for a, c in counts.items() for _ in range(c)]
    rng.shuffle(arch)
    return arch


def _category_for(arch: str, cfg: dict[str, Any], rng: np.random.Generator) -> str:
    """Declared category: surge merchants sell festive goods, fraud hides behind small retail."""
    cats = cfg["sim"]["categories"]
    if arch == "festival_surge":
        return str(rng.choice(["bakery", "grocery", "electronics"], p=[0.6, 0.2, 0.2]))
    if arch == "adaptive_mimic":
        return "bakery"
    if arch in cfg["sim"]["fraud_archetypes"]:
        return str(rng.choice(["bakery", "grocery", "restaurant", "pharmacy"]))
    names = list(cats)
    return str(rng.choice(names, p=np.array([cats[c]["share"] for c in names])))


def _groups(idx: list[int], size_range: list[int], rng: np.random.Generator) -> list[list[int]]:
    """Split merchant indices into groups (chains or rings) of size within size_range."""
    groups, i = [], 0
    while i < len(idx):
        size = int(rng.integers(size_range[0], size_range[1] + 1))
        groups.append(idx[i:i + size])
        i += size
    if len(groups) > 1 and len(groups[-1]) < size_range[0]:
        groups[-2].extend(groups.pop())                   # merge a too-small leftover group
    return groups


def build_merchants(cfg: dict[str, Any], n: int, n_days: int,
                    rng: np.random.Generator) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Return (merchant table, hidden simulation parameters per merchant)."""
    sim = cfg["sim"]
    cities = sim["cities"]
    city_names = [c[0] for c in cities]
    city_w = np.array([2.0 if c[2] == 1 else 1.0 for c in cities])
    archetypes = [h["archetype"] for h in HEROES] + _archetype_list(cfg, n - len(HEROES), rng)

    plans: list[dict[str, Any]] = []
    for i, arch in enumerate(archetypes):
        hero = HEROES[i] if i < len(HEROES) else {}
        cat = hero.get("category") or _category_for(arch, cfg, rng)
        cprof = sim["categories"][cat]
        city = hero.get("city") or str(rng.choice(city_names, p=city_w / city_w.sum()))
        p: dict[str, Any] = {
            "merchant_id": hero.get("merchant_id", f"M{i:04d}"),
            "name": hero.get("name", f"{rng.choice(NAME_PREFIX)} {CATEGORY_NOUN[cat]}"),
            "category": cat, "city": city, "city_idx": city_names.index(city),
            "archetype": arch, "label": int(arch in sim["fraud_archetypes"]),
            "base_daily": hero.get("base_daily", cprof["base_daily"] * float(rng.lognormal(0, 0.5))),
            "diwali_mult": cprof["diwali_mult"], "onboard_day": -1, "is_front": False,
            "ring_id": -1, "bet_scale": float(rng.uniform(*sim["bet_scale"])),
            "mule_intensity": sim["mule_betting_intensity"],
            "bet_price_points": hero.get("bet_price_points", sim["betting"]["price_points"]),
            "fast_payout": bool(rng.random() < sim["legit_fast_payout_share"]),
            "is_franchise": False,
        }
        if arch == "festival_surge":
            p["diwali_mult"] = hero.get("surge_mult", float(rng.uniform(*sim["surge_mult"])))
        elif arch == "growing":
            p["growth_total"] = float(rng.uniform(*sim["growth_total"]))
        elif arch == "new_merchant":
            p["onboard_day"] = n_days - int(rng.integers(*sim["new_merchant_age_days"]))
        elif arch == "slow_drift":
            frac = hero.get("drift_start_frac", rng.uniform(*sim["drift_start_frac"]))
            p["drift_start"] = int(frac * n_days)
            p["drift_ramp"] = hero.get("drift_ramp", int(rng.integers(*sim["drift_ramp_days"])))
        elif arch == "sleeper":
            p["wake_day"] = int(rng.uniform(*sim["sleeper_wake_frac"]) * n_days)
            p["dormant_mult"] = sim["sleeper_dormant_mult"]
            p["burst_mult"] = float(rng.uniform(*sim["sleeper_burst_mult"]))
        elif arch == "mule_network":
            p["is_front"] = hero.get("is_front", False)
        p["has_website"] = hero.get("has_website", bool(rng.random() < sim["website_share"]))
        style = hero.get("website_style")
        if style is None:
            if p["label"] == 1:
                style = "gaming" if rng.random() < sim["gaming_text_share"] else "clean"
            else:
                style = "generic" if rng.random() < 0.1 else "clean"
        p["website_text"] = website_text(rng, cat, style) if p["has_website"] else ""
        p["device_ids"] = [_hex(rng, "dev") for _ in range(int(rng.integers(1, 3)))]
        p["bank_account_hash"] = _hex(rng, "bank")
        p["ip_cluster"] = f"{city}_ip{int(rng.integers(0, 8))}"
        p["address_hash"] = _hex(rng, "addr")
        p["gstin_hash"] = _hex(rng, "gst")
        plans.append(p)

    _link_identities(plans, cfg, rng)
    table = _to_table(plans, cfg, n_days, rng)
    return table, plans


def _link_identities(plans: list[dict[str, Any]], cfg: dict[str, Any], rng: np.random.Generator) -> None:
    """Create shared identifiers: franchise chains, families sharing a device, and mule rings."""
    sim = cfg["sim"]
    by_arch: dict[str, list[int]] = {}
    for i, p in enumerate(plans):
        if i >= len(HEROES):
            by_arch.setdefault(p["archetype"], []).append(i)

    for chain in _groups(by_arch.get("franchise", []), sim["franchise_size"], rng):
        head = plans[chain[0]]                                # outlets share GST, some share address
        for j, i in enumerate(chain):
            plans[i].update(category=head["category"], name=head["name"], is_franchise=True,
                            gstin_hash=head["gstin_hash"],
                            website_text=head["website_text"], has_website=head["has_website"])
            if j < 2:
                plans[i]["address_hash"] = head["address_hash"]

    for pair in _groups(by_arch.get("family_shared_device", []), [2, 2], rng):
        for i in pair[1:]:
            plans[i]["device_ids"] = [plans[pair[0]]["device_ids"][0]] + plans[i]["device_ids"][1:]

    rings = _groups(by_arch.get("mule_network", []), sim["mule_ring_size"], rng)
    for r, ring in enumerate(rings):
        device, bank = _hex(rng, "dev"), _hex(rng, "bank")
        ip = f"ring{r}_ip"
        for j, i in enumerate(ring):
            p = plans[i]
            p.update(ring_id=r, ip_cluster=ip, is_front=(j == 0))
            p["device_ids"] = [device] + p["device_ids"][1:]
            if j < max(2, len(ring) - 1):                     # most (not all) members share a bank
                p["bank_account_hash"] = bank
    for i, p in enumerate(plans[:len(HEROES)]):               # hero front store joins ring 0
        if p["archetype"] == "mule_network" and rings:
            anchor = plans[rings[0][-1]]
            p["ring_id"], p["ip_cluster"] = 0, anchor["ip_cluster"]
            p["device_ids"] = [anchor["device_ids"][0]] + p["device_ids"][1:]


def _to_table(plans: list[dict[str, Any]], cfg: dict[str, Any], n_days: int,
              rng: np.random.Generator) -> pd.DataFrame:
    """Public merchant table (what a payment aggregator would hold) + label/archetype for eval."""
    end = pd.Timestamp(cfg["sim"]["end_date"])
    rows = []
    for p in plans:
        if p["onboard_day"] >= 0:
            onboard = end - pd.Timedelta(days=n_days - 1 - p["onboard_day"])
        else:
            onboard = end - pd.Timedelta(days=int(rng.integers(150, 1500)))
        rows.append({
            "merchant_id": p["merchant_id"], "name": p["name"], "declared_category": p["category"],
            "city": p["city"], "onboard_date": onboard.normalize(), "has_website": p["has_website"],
            "website_text": p["website_text"], "device_ids": p["device_ids"],
            "bank_account_hash": p["bank_account_hash"], "ip_cluster": p["ip_cluster"],
            "address_hash": p["address_hash"], "gstin_hash": p["gstin_hash"],
            "is_franchise": p["is_franchise"], "label": p["label"], "archetype": p["archetype"],
        })
    return pd.DataFrame(rows)

