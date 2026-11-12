source: merchantdna/decision/ladder.py
sha1: 26de4dbedb5a
title: Action ladder — the proportionate response by expected cost
mode: line

Five rungs: Monitor, Soft step-up (ask the merchant), Rolling reserve / settlement hold, Limit reduction, Suspend + escalate. Each rung prevents a share of the harm of a missed fraud and causes a share of the cost of disrupting an honest merchant. The recommended rung is the one with the highest expected net benefit at the merchant's probability of drift. The costs are policy parameters (sliders in the Model Lab), not model outputs.

### 1-6
Docstring with the formula.

### 7-12
Imports.

### 13-14
Spacing.

### 15-19
`tier`: LOW / MEDIUM / HIGH from the 0–100 score, with the two thresholds from the config (15 and 50). Tiers are for humans to read at a glance; the action comes from the cost calculation below.

### 20-21
Spacing.

### 22-27
`net_benefits`: the harm of a missed fraud and the cost of disrupting an honest merchant default to the config values (₹5 lakh and ₹6 lakh) but can be overridden by the sliders.

### 28-29
The "prevented" and "disruption" shares of each rung from the config (Monitor 0/0, … Suspend 1/1).

### 30-31
Broadcast: for every merchant (rows) and rung (columns), net benefit = P × harm × prevented − (1 − P) × cost × disruption.

### 32-33
Spacing.

### 34-38
`choose_rungs`: analyst capacity defaults to the config (25 per cycle).

### 39-42
The best rung per merchant by net benefit, with its name and value.

### 43-46
Merchants whose best rung is above Monitor need review; order them by net benefit; the first `capacity` of them fit in this cycle's queue and the rest wait.

### 47
Return.

### 48-49
Spacing.

### 50-55
`rung_thresholds`: sweep P from 0 to 1 and record the lowest P at which each rung becomes the best choice — the numbers the Model Lab prints next to its sliders ("Settlement hold from risk ≥ 40").
