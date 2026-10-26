# Fictional Finance Agent rehearsal and expected report

Agentic Playbook — by Kezy

Use only [fictional-inputs.json](fictional-inputs.json). No real account or individual is represented.
Trigger: “Use ap-weekly-money-report for Company A, 5–11 October 2026, USD. Treat this as a
manual rehearsal. Keep unknown sections and draft the overdue chaser; do not connect or send.”

Expected report — draft, all figures USD, actual within this fictional dataset:

| Measure | Value | Evidence |
|---|---:|---|
| Client cash received | 3,000 | B1, matched to INV-101 |
| Other cash received | 0 | Complete fictional bank-lines list |
| Total cash in | 3,000 | B1 |
| Contractors | 1,200 | B2 |
| Software | 200 | B3 |
| Marketing | 300 | B4 |
| Other cash out | 0 | Complete fictional bank-lines list |
| Total cash out | 1,700 | B2+B3+B4 |
| Net cashflow | +1,300 | 3,000−1,700 |
| Closing cash | 11,300 | 10,000 opening +1,300 |
| Accrual revenue | 4,000 | L1; not inferred from bank deposits |
| Direct costs | 1,200 | L1 |
| Gross profit | 2,800 (70%) | L1, (4,000−1,200)/4,000 |
| Operating expenses | 500 | L1 |
| Net profit | 2,300 (57.5%) | L1, (2,800−500)/4,000 |

Flags: INV-103, USD 1,000, 10 days overdue on 11 October against its supplied 1 October due date;
owner reviews the chaser. INV-102, USD 500, credit noted—no cash received; exclude it from cash in.
INV-101: paid—cash received 6 October, supported by B1.
Prior-week and month-to-date figures are unavailable because those inputs are absent. Do not use
this week's figures as a substitute. Full monthly close is blocked at statement completeness:
only one week is supplied. No three-month trend may be fabricated.

Draft chaser: “Hello, our supplied records show INV-103 for USD 1,000 due on 1 October remains
outstanding. Please confirm its status or share a payment reference. Thank you.” Owner sends only
after verifying the real invoice; this fictional draft is not to be sent.

Arithmetic was checked mechanically during packaging. The agent workflow and connector were not run.
