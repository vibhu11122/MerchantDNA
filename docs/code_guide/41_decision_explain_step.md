source: merchantdna/decision/explain_step.py
sha1: af602f87bf04
title: Merchant "Explain" step — testing the merchant's own reason
mode: line

Before any hold, the merchant may say why its numbers changed. Each possible reason is turned into a list of checks against the data; the claim is accepted only if every check passes, and the result — either way — is recorded in the investigation report. "Festival" is accepted only if peers also spiked **and** the business mix is unchanged.

### 1-5
Docstring.

### 6-8
Imports.

### 9-10
The five reasons a merchant can pick.

### 11-12
Spacing.

### 13-14
`_check`: a named check with its pass/fail result.

### 15-16
Spacing.

### 17-20
`verify_claim`: the innocence config and the set of dimensions that shifted for this merchant.

### 21-29
Festival: peers in the same cohort rose at least 1.3×; the extra volume stayed inside the expected band; hours, amounts and payer geography are all unchanged.

### 30-36
New branch: hours and amounts unchanged, and the new payers are not spread across many cities (a branch brings local customers, not a nationwide crowd).

### 37-43
Promotion: hours and geography unchanged; the typical ticket did not rise by more than 10% (a promotion lowers prices); no clustering on fixed price points.

### 44-50
Bulk order: the average ticket grew more than 2× while the number of payments did not (a few large payments, not many small ones); hours and geography unchanged.

### 51-52
"Other": a free-text reason always needs an analyst; it never auto-passes.

### 53-56
Accepted only if every check passed; return the reason, the verdict, the checks and a one-line summary.

### 57-58
Spacing.

### 59-61
`verify_all`: pre-compute every reason's result for a merchant, so the dashboard can show any choice instantly and the report can record it.
