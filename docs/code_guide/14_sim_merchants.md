source: merchantdna/sim/merchants.py
sha1: fea8f1fe20ee
title: Merchants — the public merchant table and the hidden plan
mode: line

This module creates two things for every merchant: the **public table** a payment aggregator would actually hold (name, declared category, city, onboarding date, website text, device ids, bank hash, IP cluster, address and GST hashes) and a **hidden plan** dict the simulator uses to generate behaviour (betting intensity, drift start, ring membership, and so on). The hidden plan never reaches the models. The public table carries `label` and `archetype` purely for evaluation; `utils.io.read_merchants_for_models` strips them.

### 1-9
Imports. `HEROES` is imported so the demo merchants are created first.

### 10
Blank.

### 11-14
Name parts: a random prefix plus a category noun ("Lakshmi Kirana Store").

### 15-28
A small vocabulary per category used to write synthetic website blurbs.

### 29-31
Generic business words (used by every site) and the gaming vocabulary a betting front might leak ("jackpot", "odds", "withdrawal"). The website classifier has to learn these from data; they are not hard-coded anywhere in the models.

### 32-33
Spacing.

### 34-36
`_hex`: an opaque random identifier such as `dev_3fa9c1d2e4b5a697`, used for devices, bank accounts, addresses and GST numbers.

### 37-38
Spacing.

### 39-41
`website_text` writes a 30-word blurb by sampling words from pools. Split the three vocabularies into word lists.

### 42-47
Three styles: "gaming" mixes 35% category words, 25% generic, 40% gaming words; "generic" is mostly boilerplate (an honest site with little category signal); "clean" is mostly category words.

### 48-49
For each of the 30 words, choose a pool according to `probs`, then a random word from that pool, and join with spaces.

### 50-51
Spacing.

### 52-53
`_archetype_list` turns the archetype shares in the config into exact counts for the non-hero merchants.

### 54-55
Round each share × n to an integer count.

### 56-57
Guarantee that every fraud archetype appears at least once (a mule ring needs at least 3 members) so `--small` runs still contain every case.

### 58
Give any rounding surplus or deficit to the `normal` archetype so the counts sum to exactly n.

### 59-61
Expand the counts into a list of names, shuffle so archetypes are not grouped by id, and return.

### 62-63
Spacing.

### 64-66
`_category_for` assigns a declared category to a non-hero merchant.

### 67-68
Festival-surge merchants sell festive goods: 60% bakeries, 20% grocery, 20% electronics.

### 69-70
The adaptive mimic always claims to be a bakery (the problem statement's case).

### 71-76
Honest hard negatives: night owls are restaurants or pharmacies, nationwide sellers are bakery/grocery/electronics, fixed-menu and sports-bar merchants are restaurants.

### 77-78
Other fraud archetypes hide behind small retail categories.

### 79-80
Everyone else is drawn in proportion to the category `share` values in the config.

### 81-82
Spacing.

### 83-92
`_groups` cuts a list of merchant indices into consecutive groups whose size is drawn from `size_range` (franchise chains of 3–5, rings of 3–6). If the last group is too small it is merged into the previous one.

### 93-94
Spacing.

### 95-97
`build_merchants` is the entry point: returns the public table and the list of hidden plans.

### 98-101
City list from the config: names, and a weight that makes tier-1 cities twice as likely as tier-2.

### 102
The archetype list is the heroes' archetypes followed by the random list for the remaining merchants, so heroes are merchants 0, 1 and 2.

### 103
Blank.

### 104-109
Loop over merchants. `hero` is the hero dict for the first three and empty otherwise; `hero.get(...)` therefore gives hero values precedence everywhere. Category and city come from the hero or are drawn; `cprof` is the category profile from the config.

### 110-131
The hidden plan. Highlights: `merchant_id` is `M0007`-style; `label` is 1 only for fraud archetypes; `base_daily` is the category's base rate times a lognormal factor so merchants differ in size; `bet_scale` (1–2×), `bet_weight` (fraud intensity 0.3–0.8), `local_cover` (share of bets paid by locals, 0.2–0.6) and `pp_strength` (how strongly bets cluster on price points, 0.4–1.0) make each fraud merchant different; `fast_payout` is drawn with a higher probability for fraud (60%) than for honest merchants (10%), never as a certainty; `bettor_community` picks one of four separate bettor pools; the remaining keys hold the honest defaults (category hourly profile, price points, 5% non-local payers, no match effect) that the variants below may override.

### 132
Apply the archetype-specific tweaks (hard negatives and the mimic), defined further down.

### 133-148
Archetype parameters. Festival-surge: the Diwali multiplier becomes 8–12× (10 for SweetCrust) instead of the category's normal 1.8×. Growing: total growth 1.5–2.5×. New merchant: onboarded 10–40 days before the end. Slow drift: start day as a fraction of the period, ramp of 28–42 days. Sleeper: wake day at 65–80% of the period, dormant at 10%, burst 3–5×. Mule network: `is_front` from the hero dict (QuickKart) or False.

### 149-156
Website. Each merchant has a website with probability `website_share` (55%), fraud and honest alike, so the mere absence of a site carries no information. Style: heroes specify theirs; otherwise a fraud site leaks gaming words only half the time, and 10% of honest sites are generic boilerplate. The text is generated only if the merchant has a site.

### 157-162
Identifiers: one or two device ids, a bank hash, one of eight IP clusters per city, an address hash and a GST hash. Append the plan.

### 163
Blank.

### 164-166
Create the shared identifiers (franchises, families, rings), build the public table, return both.

### 167-168
Spacing.

### 169-171
`_apply_variant` applies archetype-specific overrides; `hn` is the hard-negative config block.

### 172-174
Night owl: blend the category's hourly profile 50/50 with a night-heavy profile, so an honest restaurant has real night share.

### 175-177
Nationwide seller: 45% of payers from other cities and 25% travellers — honest, but geographically it looks like a betting front.

### 178-181
Fixed-menu restaurant: honest fixed prices at ₹499 and ₹999. Sports bar: 1.7× volume on match days.

### 182-186
Adaptive mimic: amount jitter 15%, weaker price-point clustering (35%), half of its bets paid by locals, no match-day lift, and *slow* payouts — it avoids every obvious tell.

### 187-189
Betting price points: a hero may set its own (FreshOven: mostly ₹999); otherwise the shares are scaled by `pp_strength`, so some frauds cluster hard and others barely.

### 190-191
Spacing.

### 192-198
`_link_identities`: group the non-hero merchants by archetype (heroes are handled explicitly).

### 199
Blank.

### 200-207
Franchise chains: all outlets copy the head's category, name, website and GST number (a legitimately shared identifier), and the first two also share the address. The network model must treat these as *weak* links.

### 208
Blank.

### 209-211
Family shared device: pairs of honest merchants where the second shares the first's primary device — a hard negative for the network pillar.

### 212
Blank.

### 213-222
Mule rings: each ring gets one shared device, one shared bank account and one IP cluster. Every member uses the shared device as its primary device; most (not all) share the bank; member 0 of each ring is its front store (`w = 0` in the daily plan).

### 223-227
The hero front store (QuickKart) joins ring 0: it takes the ring's IP cluster and primary device from the ring's last member, but *not* the bank — the link is there, but not the strongest possible.

### 228-229
Spacing.

### 230-233
`_to_table` builds the public table.

### 234-240
Onboarding date: new merchants onboard inside the period; everyone else 150–1500 days before the end.

### 241-248
One row per merchant with exactly the columns in CLAUDE.md §4, including `label` and `archetype` for evaluation only. Return the DataFrame.

### 249
Trailing blank line.
