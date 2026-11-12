source: merchantdna/features/volume_time.py
sha1: 12fc915c89c9
title: Volume, time-of-day and burstiness features
mode: line

Three feature families. Volume is what a static rule sees, kept separate so the Innocence Engine can neutralise it. Time-of-day is the first behavioural fingerprint (bakeries trade in the morning, betting at night). The burst index measures *how* payments arrive within an hour, independent of how many there are.

### 1-7
Imports.

### 8-9
Spacing.

### 10-11
`volume_features` for a window ending on `end_day`.

### 12-14
Window lengths from the config (30 and 7 days); the short sub-window; a groupby per merchant. `observed=False` keeps merchants with no rows (they are categoricals) so the frame always has 800 rows.

### 15-21
Counts and GMV over the long and short windows, and the number of active days.

### 22
Growth = short-window daily rate / long-window daily rate. Values above 1 mean the last week was busier than the month.

### 23-24
Daily Fano factor: variance / mean of the per-day counts (a (merchant × day) grid filled with zeros). Steady merchants are near 1; sleepers and surge merchants are high.

### 25
Return.

### 26-27
Spacing.

### 28-31
`time_features`: night hours (0–5) and evening hours (19–23) from the config.

### 32-35
Count transactions per (merchant, hour), make sure all 24 columns exist, divide by the row total to get shares, and name the columns `h00`–`h23`. This 24-bin profile is part of the DNA.

### 36-38
Night share and evening share are sums over the relevant bins (`iloc` uses positions, which equal hours here).

### 39-41
Weekend share: mean of the weekend flag per merchant. Return.

### 42-43
Spacing.

### 44-49
`burst_features` docstring: the Fano factor of 10-minute bucket counts within each active hour. A Poisson stream has Fano ≈ 1 regardless of volume, so a Diwali rush does not look bursty, while bets landing minutes after a wicket do.

### 50-52
Bucket size (10 minutes), buckets per hour (6), and each transaction's bucket within its hour.

### 53-55
Count per (merchant, day, hour, bucket), then sum counts and squared counts per (merchant, day, hour). This replaces an earlier `lambda`-based aggregation that took 32 seconds per window; this vectorised form takes 0.4 s.

### 56-58
Mean and variance over the 6 buckets (E[n²] − E[n]²), then Fano = var / mean per active hour.

### 59-61
Average the hourly Fano values weighted by that hour's transaction count, so busy hours dominate, and return it as `burst_index`.
