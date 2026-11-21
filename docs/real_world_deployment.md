# From prototype to production: can MerchantDNA work in real life?

> Research notes for Round 2 (Feasibility 15%, Q&A 10%). Compiled 21 Nov 2026 from regulator pages, law-firm summaries and news reports. We did not read every Act in full. Items marked **(verify)** must be checked against the primary text before you quote them as fact.

## 1. Verdict

**Feasible, and largely already required by regulation.** A payment aggregator (PA) such as PayU must already monitor every merchant against its business profile. MerchantDNA is one concrete way to do that. It does not punish honest festival spikes, and every action leaves an audit trail.

It runs **after authorisation, as a daily batch** inside the PA's risk stack. It is not on the payment path, so checkout latency is unaffected.

## 2. Why a payment aggregator must do this

| Source | What it requires | MerchantDNA component |
|---|---|---|
| **RBI Regulation of Payment Aggregators Directions, 2025** (issued 15 Sep 2025; RBI page shows a version updated 11 Nov 2026) [1][2] | Continuous monitoring of merchant transactions for consistency with the merchant's **business profile**. Migration to a higher due-diligence category **based on transaction pattern**. Risk-based payment limits per merchant. Checks that merchants do not sell prohibited products. | Behavioural category verifier, drift score, tiers; "Soft step-up" = re-verification; "Limit reduction" rung |
| **Promotion and Regulation of Online Gaming Act, 2025** (in force 22 Aug 2025) [4][5] | Banks, wallets and payment intermediaries may not process transactions for online money games. Penalties fall on operators and on the financial institutions that serve them. | Motivating case: purpose drift towards betting |
| **Online Gaming Rules, 2026** (reported in force 1 May 2026) [5][6] | The Authority can direct banks and payment intermediaries to halt transactions linked to real-money games. | Fast evidence pack per merchant for when a direction arrives |
| **PMLA / FIU-IND** [8][9] | Payment system operators are "financial institutions" under PMLA and must file STRs. PAs file through **FINGate 2.0**. The filing deadline is generally 7 working days after concluding a transaction is suspicious **(verify against the PML Rules)**. | Auto-drafted STR, filed only after an analyst reviews it |

**Evidence that the problem is real:**

- **Parimatch (ED, Aug 2025)** [7][10]
  - The ED froze about ₹110 crore and seized about 1,200 mule credit cards.
  - The ED alleges that firms whose PA licence applications RBI had rejected acted as "technology service providers". They let the platform collect bets over UPI through mule accounts registered under e-commerce and payment-solution names.
  - This is the "bakery that takes bets" pattern. These are allegations, not court findings.
- **RBI enforcement:** RBI fined Cashfree Payments ₹3.10 lakh (9 Mar 2026) for not complying with the PA/PG guidelines [3]. Supervisors are checking.
- One report says the ED's 2024–25 annual report mentions mule accounts listed as merchants with large PAs. **(Unconfirmed, do not name companies.)**

## 3. What already exists, and our gap

| Existing system | What it does | Gap MerchantDNA fills |
|---|---|---|
| **MuleHunter.AI** (RBI Innovation Hub; used by 29 banks) [11] | Risk-scores **bank accounts** as possible mules, from transaction and profile data | Works at the bank-account level, not on a PA's merchants against their declared category |
| **Digital Payments Intelligence Platform (DPIP)** (RBI/RBIH pilot, 7 banks) [11] | Real-time risk score on the **beneficiary** before a payment executes | Still a pilot, and judges fraud on each payment. It does not track how a merchant's behaviour drifts over weeks |
| **NPCI fraud monitoring** [12] | AI/ML alerts and declines for banks on UPI | Not designed to tell whether a merchant behaves like its claimed business |
| **Transaction-laundering vendors** (e.g. LegitScript, under Mastercard BRAM / Visa VIRP programmes) [13] | Website crawling, test purchases, mismatched merchant descriptors | Based on the website and paperwork. A merchant with a clean website and genuine documents passes |

**Our pitch:** we judge a merchant on its *behaviour and its payers* against peers in the same declared category. Before flagging, we test innocent explanations such as a festival, and the response is proportionate. None of the systems above focus on this.

## 4. Production architecture

| Prototype | Production counterpart |
|---|---|
| `merchantdna/sim/` (synthetic data) | The PA's data lake: transactions, **hashed** payer VPAs/cards, device fingerprints from the checkout SDK, settlements, MCC, onboarding KYC, website URL |
| `merchantdna/features/` | Scheduled daily job (Spark or dbt on the warehouse) that writes to a feature store; 7-day and 30-day windows unchanged |
| `merchantdna/models/` | Retrained monthly and registered in a model registry with version, data snapshot and sign-off. Every merchant is scored daily |
| Innocence Engine | Same logic. The peer cohorts and festival calendar come from the PA's own data |
| Network pillar | Graph built from the PA's own onboarding identifiers (device, bank account, IP, GSTIN) |
| `merchantdna/decision/` action ladder | Writes cases into the PA's existing case-management or AML tool. Costs and capacity set by the risk committee |
| Merchant "Explain" step | An in-dashboard or email request to the merchant, with the answer checked automatically |
| STR draft | Pre-fills the FINGate 2.0 STR. An analyst edits and files it, never the system |
| Streamlit dashboard | The analyst console |

## 5. Replacing synthetic labels

Real labels come from:

- Law-enforcement and ED notices or freeze requests
- Cybercrime complaints (NCRP / I4C) linked to a merchant
- Chargeback and dispute patterns
- RBI or the Gaming Authority's directions to block transactions
- Analysts' own decisions on cases

Start with the existing **unsupervised and peer-relative signals**, which need no labels. Add the fusion stacker once a few hundred confirmed cases exist. Then retrain on analysts' decisions (active learning). The simulator stays as a **test bench** for new fraud patterns.

## 6. Rollout

1. **Shadow mode, about 3 months.** Score one category (for example food and bakery) daily, take no actions, and compare with the PA's current rules. Measure false-alarm rate on festival merchants and how many days earlier we catch cases.
2. **Soft step-up only.** Turn on the "ask the merchant to explain" rung, which is low-harm.
3. **Holds and limits.** Allowed only with analyst approval and a grievance or appeal channel for merchants.
4. **Data sharing.** Explore sharing payer-overlap signals with NPCI or the DPIP pilot.

## 7. Hard problems, stated honestly

1. **Partial payer view.** A PA sees payers only at its own merchants. Betting rings that spread across PAs are partly invisible, so full coverage needs industry data sharing (NPCI/DPIP).
2. **Privacy (DPDP Act 2023 + Rules notified Nov 2025)** [14][15]. Purpose limitation, retention limits and security safeguards apply. We use hashed payer IDs only, and data is used only to monitor merchants. The exact legal ground for processing data for fraud prevention **(verify with counsel)**.
3. **Fairness to honest merchants.** A wrong settlement hold hurts a small business. Our answers are the Innocence Engine, plain-English reasons, the Explain step and a human decision.
4. **Adversarial adaptation.** The mimic stress test shows fraudsters can fake hours and prices. Payer-side signals are harder to fake, but plan to retrain regularly and red-team the system.
5. **Model governance.** The PA's model-risk process, audit logs and periodic validation. Every score has drivers and evidence, and every action has a report.
6. **Legal uncertainty.** Challenges to the Gaming Act are pending before the Supreme Court [5]. Our framing ("purpose drift", not "betting") holds either way.

## 8. One-line Q&A answer

> "RBI already requires PAs to monitor merchants against their business profile. MerchantDNA is how a PA meets that requirement without punishing honest Diwali spikes. It starts in shadow mode, and a human always decides."

## Sources

1. RBI – Regulation of Payment Aggregators Directions, 2025: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12896&Mode=0
2. Cyril Amarchand Mangaldas client alert on the consolidated PA framework: https://www.cyrilshroff.com/wp-content/uploads/2025/10/Client-Alert-RBI-Introduces-Consolidated-Framework-for-Payment-Aggregators-3.pdf
3. RBI press release (Cashfree penalty): https://rbi.org.in/scripts/FS_PressRelease.aspx?fn=2766&prid=62386
4. Online Gaming Act 2025 (India Code): https://www.indiacode.nic.in/bitstream/123456789/22148/1/a2025-32.pdf
5. Mondaq – Online Gaming Act 2025 and Rules 2026: https://www.mondaq.com/india/social-media/1785870/the-promotion-and-regulation-of-online-gaming-act-2025-and-the-promotion-and-regulation-of-online-gaming-rules-2026
6. Bar & Bench – banks must block real-money game payments: https://www.barandbench.com/amp/story/news/law-policy/banks-must-block-payments-to-real-money-games-under-new-online-gaming-rules-2026
7. Business Standard – ED freezes ₹110 cr in Parimatch case: https://www.business-standard.com/amp/india-news/ed-freezes-parimatch-accounts-110-cr-pmla-illegal-online-betting-125081401139_1.html
8. FIU-IND FINGate 2.0 user manual: https://fiuindia.gov.in/pdfs/quicklinks/User_Manual_FINGate2.0.pdf
9. FIU-IND FINnet 2.0 AI upgrade: https://indianstartupnews.com/news/fiu-unveils-ai-infused-system-to-combat-money-laundering-terrorism-financing-4545079
10. g2g.news – rejected PA applicants facilitated Parimatch payments: https://g2g.news/online-gaming-laws/payment-aggregator-applicants-rejected-by-rbi-facilitated-payments-for-illegal-betting-portal-parimatch/
11. RBI publication on MuleHunter.AI and DPIP: https://rbi.org.in/SCRIPTS/PublicationsView.aspx?id=23810
12. eWeek – NPCI turns to AI as fraud rules tighten: https://www.eweek.com/news/npci-ai-payments-fraud-rules-apac-india/
13. LegitScript – transaction laundering detection: https://legitscript.com/solutions/merchant-risk-solutions/transaction-laundering-detection/
14. PIB – DPDP Rules 2025: https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf
15. Grant Thornton – DPDP Rules brochure: https://www.grantthornton.in/globalassets/1.-member-firms/india/assets/pdfs/flyers/dpdpa-rules-detailed-brochure_final-25th-november-2025-1.pdf
