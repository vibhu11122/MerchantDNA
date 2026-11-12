# Demo script

Start with `make demo` (rebuilds everything, ~3 min, then opens the app) or `make app` if artefacts exist. Use a 1600 px-wide window; fonts are sized for a projector.

## A. Two-minute video (Round 1)

| Time | Screen | Say |
|---|---|---|
| 0:00–0:15 | Home | "A bakery onboards with genuine documents, then collects betting money. Each payment looks normal. Festival spikes look suspicious. Rules fail both ways. MerchantDNA learns what a legitimate bakery *does*, and tests every deviation against legitimate explanations before flagging." |
| 0:15–0:35 | Home → hero cards | "Three merchants. SweetCrust: real bakery, 10× Diwali spike — LOW, cleared. FreshOven: same paperwork, drifting — HIGH. QuickKart: looks normal, shares a device with a ring — MEDIUM, 'ask the merchant'. None of these scores are hard-coded; they come out of the models." |
| 0:35–1:00 | Merchant Deep Dive (FreshOven) | Point at the drivers bar: "Payers from other cities, payers who pay in many cities, 75% of payments at exactly ₹499/999/1999, 12% at midnight. Innocence Engine: volume is not the issue — the *mix* changed, and a festival cannot explain a different mix." |
| 1:00–1:25 | DNA Map, press ▶ | "Every dot is a behaviour fingerprint. Watch the weeks: FreshOven walks out of the bakery cluster. SweetCrust's Diwali volume explodes but its DNA stays with the bakeries." |
| 1:25–1:45 | Network Graph (QuickKart) | "QuickKart shares a device and IP with three merchants scoring 67–83, and 3% of its payers are theirs. Enough to ask, not enough to suspend." |
| 1:45–2:00 | Model Lab table | "On 720 held-out merchants: PR-AUC 0.97 vs 0.78 for Isolation Forest and 0.20 for rules. Zero false alarms on festival merchants versus 79% for rules. Synthetic data, honestly reported. Signals, not proof — the analyst decides." |

## B. Five-minute stall walkthrough (Round 2)

1. **Hook (30 s).** Home page. The one-line pitch. "Ask me to break it at the end."
2. **The honest merchant (60 s).** Deep Dive → SweetCrust. Timeline: the Diwali spike sits *inside* the blue expected band because peers rose too. Verdict: Cleared. Hour × day heatmap: same hours as always.
3. **The drifted merchant (60 s).** Deep Dive → FreshOven. Same timeline shape — but the band does not cover it, and the Innocence verdict says "business mix changed: hours, amounts, payers". Amount histogram vs peers: the ₹999 spike. Investigation Report → choose "festival" as the merchant's explanation → watch the checks fail.
4. **The signature visual (45 s).** DNA Map, ▶. Let it run once. Pause at the last frame.
5. **The ring (45 s).** Network Graph → QuickKart, 2 hops. Hover an edge: "Shares device + ip". Scroll to the community table.
6. **Proof and honesty (45 s).** Model Lab → table and ablation. Say out loud: "Payer features are the strongest pillar; the Innocence Engine barely moves this stacker's PR-AUC but halves false alarms when bolted onto rules; the network adds explanation more than lift." Judges trust what you admit.
7. **Break it (45 s).** Model Lab → tab 1: inject a 10× Diwali spike into a genuine bakery → cleared, LOW. Switch to "an ordinary week" → "not explained" but still LOW ("volume alone never makes you high risk"). Tab 2: make FreshOven mimic a bakery → score drops from 82 to ~68, still HIGH; the payer signals still fire.
8. **Close (15 s).** Cost sliders: "Your risk appetite is a dial, not a code change." Point at the regulatory hook and hand over the Q&A sheet.

## C. Things that go wrong

- Page shows "Artefacts not found" → `make all` was not run in this clone.
- DNA Map animation looks static → press ▶; the slider at the bottom also steps frames.
- Network page is slow the first time (loads the model bundle once, then cached).
- Someone picks a random merchant and asks why it is MEDIUM → read the drivers and the evidence list; if it is a nationwide seller, say so (limitations §5).
