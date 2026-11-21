# Demo script

Start with `make demo` (rebuilds everything, ~3 min, then opens the app) or `make app` if artefacts exist. Use a 1600 px-wide window; fonts are sized for a projector.

## A. Two-minute video (Round 1)

| Time | Screen | Say |
|---|---|---|
| 0:00–0:15 | Home | "A bakery onboards with genuine documents, then collects betting money. Each payment looks normal. Festival spikes look suspicious. Rules fail both ways. MerchantDNA learns what a legitimate bakery *does*, and tests every deviation against legitimate explanations before flagging." |
| 0:15–0:35 | Home → hero cards | "Three merchants. SweetCrust: real bakery, 10× Diwali spike — LOW, cleared. FreshOven: same paperwork, drifting — HIGH. QuickKart: looks normal, shares a device with a ring — MEDIUM, 'ask the merchant'. None of these scores are hard-coded; they come out of the models." |
| 0:35–1:00 | Merchant Story (FreshOven) | Point at the drivers bar: "Payers from other cities, payers who pay in many cities, 75% of payments at exactly ₹499/999/1999, 12% at midnight. Innocence Engine: volume is not the issue — the *mix* changed, and a festival cannot explain a different mix." |
| 1:00–1:25 | DNA Map, press ▶ | "Every dot is a behaviour fingerprint. Watch the weeks: FreshOven walks out of the bakery cluster. SweetCrust's Diwali volume explodes but its DNA stays with the bakeries." |
| 1:25–1:45 | Merchant Story → Connections tab (QuickKart) | "QuickKart shares a device and IP with three merchants scoring 67–83, and 3% of its payers are theirs. Enough to ask, not enough to suspend." |
| 1:45–2:00 | Proof & Try It table | "On 720 held-out merchants: PR-AUC 0.97 vs 0.78 for Isolation Forest and 0.20 for rules. Zero false alarms on festival merchants versus 79% for rules. Synthetic data, honestly reported. Signals, not proof — the analyst decides." |

## B. Five-minute stall walkthrough (Round 2)

The app has four screens: **Home → Merchant Story → DNA Map → Proof & Try It**.

1. **Hook (30 s).** Home. Read the one-line pitch, then point at the three KPI tiles: 800 merchants, how many flagged, and 0% festival false alarms against 79% for rules. "Ask me to break it at the end."
2. **The honest merchant (45 s).** Click *Open SweetCrust* → Merchant Story. Timeline: the Diwali spike sits *inside* the purple expected band because peers rose too. Verdict: Cleared.
3. **The drifted merchant (75 s).** Switch the picker to FreshOven. Same timeline shape, but the verdict says "business mix changed: hours, amounts, payers". Read 2–3 evidence lines aloud. Open **Explain & report**, choose "festival" as the merchant's reason and watch the checks fail. Scroll to the **Draft STR**: "the analyst's paperwork is already written, but a human must tick *reviewed* before it can be downloaded."
4. **The signature visual (45 s).** DNA Map, press ▶. Let it run once and pause on the last frame.
5. **The ring (30 s).** Merchant Story → QuickKart → **Connections** tab. Hover an edge: "Shares device + ip". "Enough to ask, not enough to suspend."
6. **Proof and break it (60 s).** Proof & Try It. Point at the 3-row table. Tab 1: inject a 10× Diwali spike into a genuine bakery → cleared, LOW. Tab 2: make FreshOven mimic a bakery → the score drops but stays HIGH, because the payer signals still fire.
7. **Close (15 s).** "Signals, not proof. A human decides, and every decision leaves an audit trail." If a technical judge asks, open *For technical judges* (ablation, PR curves, cost sliders).

## C. Things that go wrong

- Page shows "Artefacts not found" → `make all` was not run in this clone.
- DNA Map animation looks static → press ▶; the slider at the bottom also steps frames.
- The Connections tab is slow the first time (it loads the model bundle once, then caches it).
- Someone picks a random merchant and asks why it is MEDIUM → read the drivers and the evidence list; if it is a nationwide seller, say so (limitations §5).
