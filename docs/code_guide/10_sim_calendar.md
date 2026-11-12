source: merchantdna/sim/calendar.py
sha1: e5642bab68e1
title: Calendar — festivals and the synthetic cricket league
mode: line

The calendar is one row per simulated day. It carries everything that legitimately changes demand (weekends, minor festivals, the Diwali window and peak) and everything a betting collector reacts to (match days, and the minute of every wicket). Diwali dates are the real 2026 dates; the cricket league is synthetic, which we say openly in `docs/decisions.md`.

### 1-7
The module docstring states the purpose. `from __future__ import annotations` lets us write modern type hints such as `dict[str, Any]` on Python 3.11 without evaluating them at import time. `Any` is used for the config dict; NumPy and pandas are the only dependencies.

### 8-9
Two blank lines between top-level definitions (PEP 8).

### 10-13
`date_range` builds the list of simulated dates. It reads `sim.end_date` from the config (the scoring "as-of" day, 11 Nov 2026), turns it into a pandas `Timestamp`, and asks pandas for `n_days` consecutive daily dates **ending** on that day. Anchoring on the end date means the Diwali window always falls inside the scoring window, whatever `n_days` is.

### 14-15
Spacing.

### 16-18
`_in_window` returns a boolean NumPy array marking the dates between `start` and `end` inclusive. The leading underscore means "private to this module". `np.asarray` converts the pandas boolean index into a plain array so it can be used for fancy indexing later.

### 19-20
Spacing.

### 21-22
`build_calendar` is the public entry point. It takes the config, the number of days and a NumPy random generator (passed in, never created here, so the whole simulation is driven by one seed).

### 23-25
Shortcut `sim` to the simulator section of the config, build the dates, and start the DataFrame with the date, a 0-based `day_idx` (used everywhere as the integer day key) and `dow` (day of week, Monday = 0).

### 26-28
Weekend flag (Saturday = 5, Sunday = 6). Two Diwali flags: the wider window (shops are busier for about ten days) and the peak (the four days around the festival itself). `*sim["diwali_window"]` unpacks the `[start, end]` list from the config into the two arguments.

### 29
Blank line separating logical steps.

### 30-34
Minor festivals. Start with a multiplier of 1 for every day; for each `[start, end, mult]` entry in the config, set that multiplier on the matching days. Keep both the multiplier (used by the simulator) and a boolean flag (used by the expected-volume model as a feature).

### 35
Blank.

### 36
Pick match days at random: each day is a match day with probability `match_day_prob` (0.4). This is where the calendar becomes synthetic.

### 37-38
Match start and end as minutes after midnight (19:30 → 1170, 23:00 → 1380).

### 39-40
`match_start` as a real timestamp per day (or `NaT`, "not a time", on non-match days). Only used for display.

### 41-44
Wicket times: on a match day, draw `wickets_per_match` (12) random minutes between start and end, sort them, and store as a Python list. Non-match days get an empty list. The betting generator later places a share of bets in the ten minutes after these times.

### 45
Return the finished calendar.
