source: merchantdna/models/website.py
sha1: ac549143c29b
title: Website classifier — the claimed-profile pillar
mode: line

Does the merchant's website read like the business it declared? A TF-IDF + logistic-regression text classifier is trained to predict the declared category from website text. If the model, having seen hundreds of bakery sites, gives *this* bakery's text a low probability of being a bakery, that is a mismatch. Merchants without a website get the median mismatch — neutral, because having no website is common and honest.

### 1-6
Docstring.

### 7-16
Imports: TF-IDF vectoriser, logistic regression, stratified K-fold and `cross_val_predict` (out-of-fold predictions), and `make_pipeline` to chain vectoriser and classifier.

### 17-18
Spacing.

### 19-23
`make_model`: TF-IDF over unigrams and bigrams (up to 2,000 features) feeding a logistic regression with regularisation strength `C` from the config. A pipeline means `fit(text, y)` does both steps.

### 24-25
Spacing.

### 26-27
`fit_website` returns the fitted model and a per-merchant table.

### 28-30
Only merchants with a website take part; `text` and `y` (declared category) are their rows.

### 31-33
Build the model and get **out-of-fold** probabilities: five stratified folds, each merchant's probabilities come from a model trained on the other four folds. Without this, a merchant's own text would influence its own score.

### 34-35
`predict_proba` columns are in sorted class order; pick, for each merchant, the probability of its *declared* class.

### 36
Fit the final model on all website text (used later only to list the words pulling away from the declared category).

### 37
Blank.

### 38-41
Output table indexed by merchant id: `website_p_declared` (NaN for no website) and `website_mismatch` = 1 − that probability.

### 42-44
Neutral fill: merchants without a website get the median mismatch across those who have one, so they are neither helped nor hurt. Return.

### 45-46
Spacing.

### 47-49
`top_terms`: for the report, which words in this site's text argue against the declared category. Pull the two pipeline steps.

### 50-52
Transform the text to its TF-IDF vector; find the declared class's row in the coefficient matrix; multiply element-wise so each word's contribution to "is this category" is its weight × its coefficient.

### 53-55
The k most negative contributions (words pulling away), mapped back to feature names. For FreshOven this yields words such as "jackpot" or "withdrawal".
