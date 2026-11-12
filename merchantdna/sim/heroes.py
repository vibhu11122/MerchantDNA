"""The three demo ("hero") merchants. Only their *behaviour* is fixed here, never their score."""
from __future__ import annotations

HEROES: list[dict] = [
    {   # Genuine bakery with a 10x Diwali spike: expected LOW risk (cleared by the Innocence Engine)
        "merchant_id": "M0000", "name": "SweetCrust Bakery", "category": "bakery",
        "city": "Bengaluru", "archetype": "festival_surge", "surge_mult": 10.0,
        "base_daily": 60.0, "has_website": True, "website_style": "clean",
    },
    {   # Bakery that drifts into collecting bets from mid-period: expected HIGH risk
        "merchant_id": "M0001", "name": "FreshOven Bakery", "category": "bakery",
        "city": "Pune", "archetype": "slow_drift", "drift_start_frac": 0.5, "drift_ramp": 35,
        "base_daily": 45.0, "has_website": True, "website_style": "gaming",
        "bet_price_points": {999: 0.70, 499: 0.10, 1999: 0.05},
    },
    {   # Normal-looking grocery that shares a device + IP with a mule ring: expected MEDIUM
        "merchant_id": "M0002", "name": "QuickKart Store", "category": "grocery",
        "city": "Mumbai", "archetype": "mule_network", "is_front": True, "ring_id": 0,
        "base_daily": 80.0, "has_website": False, "website_style": "none",
    },
]
