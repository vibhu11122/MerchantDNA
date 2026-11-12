source: merchantdna/models/network.py
sha1: f9bcc7f8e525
title: Network pillar — shared identifiers and shared payers
mode: line

Two graphs. The identity graph links merchants that share a device, bank account, IP cluster, address or GST number, with an edge weight that is larger when the shared thing is rarer and when the attribute is inherently strong (a device is strong; a franchise's GST number is weak). The payer-overlap graph links merchants whose customers overlap more than chance. Suspicion then propagates over these graphs **without labels**: a merchant inherits the behavioural suspicion of its neighbours.

### 1-9
Docstring.

### 10-18
Imports: `defaultdict` and `combinations` for building edges, NetworkX, NumPy, pandas.

### 19-22
Which merchant column holds each attribute, and which attributes count as strong (device and bank).

### 23-24
Spacing.

### 25-30
`identity_graph`: read the attribute strengths from the config, start a graph with every merchant as a node.

### 31-35
For each attribute, collect the merchants holding each value (a merchant can hold several device ids, so devices are flattened).

### 36-39
For every value held by at least two merchants, the edge weight is `strength × log(N / holders)` — the IDF idea: a device shared by 2 of 800 merchants scores log(400) ≈ 6; an IP cluster shared by 50 scores log(16) ≈ 2.8 × 0.4.

### 40-42
Add (or strengthen) the edge between every pair of holders, accumulating the weight and recording *via* which attributes they are linked.

### 43
Return.

### 44-45
Spacing.

### 46-50
`payer_overlap_graph` works on the current window's transactions: unique (merchant, payer) pairs.

### 51-53
Unique payers per merchant; drop payers seen at only one merchant (no overlap possible) and payers seen at more than 50 (so common they carry no information).

### 54-56
Self-join on payer to get every merchant pair sharing a payer, keep each pair once, and count shared payers per pair.

### 57-59
Jaccard = shared / (payers of A + payers of B − shared).

### 60-64
Keep pairs with at least 5 shared payers and Jaccard ≥ 0.02; build the graph with Jaccard as the edge weight.

### 65-66
Spacing.

### 67-72
`strong_cases`: connected components over strong links only (device or bank). Used to simulate how analysts label — when one merchant in a case is reviewed, the whole case is.

### 73-74
Spacing.

### 75-78
`communities`: Louvain community detection on the weighted identity graph, returning merchant → community id. A fixed seed keeps the partition reproducible.

### 79-80
Spacing.

### 81-92
`_neighbour_risk`: for each node, the edge-weighted average of its neighbours' suspicion, with `prior` added to the denominator as a pseudo-weight on "no risk" so one weak tie to a suspicious merchant produces only a small value. Isolated nodes get 0.

### 93-94
Spacing.

### 95-99
`network_features` takes both graphs, the community map, the label-free stage-1 suspicion (a population percentile in 0–1) and the config.

### 100-101
Only the top 20% most suspicious neighbours pass anything on: the percentile is rescaled so that 0.8 → 0 and 1.0 → 1. Before this change every merchant's neighbour risk sat near 0.48 because a *typical* neighbour contributed 0.5; now ring members show about 0.74 and everyone else about 0.05.

### 102-103
Identity-neighbour risk.

### 104-105
How many of the merchant's identity links involve a device or bank account.

### 106-110
Community risk: the mean suspicion of the *other* members of the merchant's Louvain community (0 for singleton communities), and the community size.

### 111-113
Degree in the payer-overlap graph and payer-neighbour risk (with a smaller prior, because a Jaccard edge is already a strong statement). Return.
