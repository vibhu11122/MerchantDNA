source: merchantdna/models/dna_autoencoder.py
sha1: 68273741ee79
title: Merchant DNA — autoencoder embedding and drift
mode: line

An autoencoder is a neural network trained to reproduce its own input through a narrow middle layer. The middle layer here has 12 units, so every merchant's 69 SHAPE features are squeezed into 12 numbers — the "DNA". Two merchants with similar DNA do business the same way. Drift is then simply a distance: how far has this merchant's DNA moved from its own history, and how far is it from the typical DNA of its declared category.

### 1-6
Docstring.

### 7-16
Imports: sklearn's `MLPRegressor` (a plain multi-layer perceptron used as a regressor), `StandardScaler`, and the SHAPE columns.

### 17-18
Spacing.

### 19-21
`fit_autoencoder`: the config gives the layer sizes `[32, 12, 32]`, the L2 penalty and the iteration cap.

### 22-23
Standardise every feature to mean 0 / standard deviation 1 (fitted on the training rows), and clip to ±6 so a single extreme value cannot dominate the reconstruction loss.

### 24-26
The network: input → 32 → **12** → 32 → output, tanh activations, early stopping on a validation split. `ae.fit(x, x)` is the whole trick: the target *is* the input.

### 27
Return the scaler, the network, and the index of the bottleneck layer (2 for a 3-layer hidden stack: the first two weight matrices lead into it).

### 28-29
Spacing.

### 30-31
`_scaled`: apply the fitted scaler and clip, the same way as in training.

### 32-33
Spacing.

### 34-40
`embed`: run the first `bottleneck_layer` layers forward by hand — for each (weights, bias) pair, `h = tanh(h @ W + b)` — and return the 12-dimensional activations. sklearn exposes `coefs_` and `intercepts_`, so no deep-learning framework is needed.

### 41-42
Spacing.

### 43-46
`recon_error`: mean squared difference between the network's reconstruction and the input. A merchant the network cannot reproduce well has an unusual shape overall.

### 47-48
Spacing.

### 49-55
`category_centroids`: the median DNA per declared category (robust centre), and each category's typical distance from its centre (the median of its members' distances). The spread is the yardstick that turns raw distances into "how many typical distances".

### 56-57
Spacing.

### 58-61
`drift_scores` for any feature table (current window or snapshots).

### 62-64
Embed the rows; look up each row's declared category and its own history code.

### 65-69
`dna_drift_self` = distance from the history code; `dna_drift_cat` = distance from the category centroid; both divided by the category's typical spread, so 1.0 means "as far as a typical member sits from the centre". FreshOven ends at about 13×. Plus the reconstruction error.

### 70
Return the scores and the raw codes (UMAP projects the codes for the map).
