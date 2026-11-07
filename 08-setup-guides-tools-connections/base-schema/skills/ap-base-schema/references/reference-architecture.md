# Reference architecture

A real production base for a creative-production company — 11 tables (Lane, Project, Task,
Project Output, Quotation, Sales Invoice, AP Invoice, Client, Vendor, Employee, Monthly
Period). Use it as a **pattern library, never a template.** Each layer is listed with the
reason it exists, because the reason is the transferable part.

| Layer | Reference tables | Why the layer exists | Skip it when |
|---|---|---|---|
| **Spine** | project | one row per unit of work; everything points here | never — no spine means the interview isn't finished |
| Classification | lane | a category that earns its own table because you want to count/compare by it | it's a closed short list with no attributes and no counts wanted → a `TEXT` choice |
| Counterparties | client, vendor | the outside world; one row reused across many spine rows; compliance + banking payload | the business sells to walk-in strangers it never bills again |
| People | employee | the inside world; HR payload + workload counts | solo operator, no delegation |
| Money in | quotation, sales_invoice | one row per revenue document, with its own dates/amounts/proof | never — even a cash business has a revenue row |
| Money out | ap_invoice | one row per cost attributable to a spine row | no per-job variable cost — say so and move on |
| Execution | task, project_output | the doing, and the artifact delivered | work is one step by one person |
| Period | period | a physical row per month so reports have stable rows | you only ever look at totals, never trends |

## Seven decisions worth stealing (in SQL)

**1. Money never sits on the spine.** Amounts live on transaction rows; the spine's totals
are a view (see `sql-mechanics.md` `project_money`). If a human can type a total, two numbers
eventually disagree.

**2. Status derived from evidence.** The filled date *is* the switch:
`CASE WHEN paid_date IS NOT NULL THEN 'Done' ELSE 'Pending' END` in a view. Only make status a
stored column when a human genuinely makes a judgment call.

**3. Accrual and cash are two questions — answer both, labelled.** Project profit sums every
invoice raised (accrual: "did this job make money"). The monthly view sums by `paid_date`
(cash: "what moved this month"). Ask which they manage on; build both buckets; never let them
be confused.

**4. Group by month with `strftime`.** No text-sibling columns needed (that was a Lark
workaround): `GROUP BY strftime('%Y-%m', invoice_date)`.

**5. The period table.** A one-column table of month strings (`'2026-01', …`); each row pulls
a filtered `SUM` from the money tables (see `monthly_pl`). Gives a P&L row for every month and
a home for a budget column next to actual.

**6. Link when you count, plain value when you only notify.** Task's `responsible_id` is a FK
to employee because workload rolls up (`COUNT` of in-progress tasks per person). "Consult" /
"Inform" are plain text — nobody needs a Consult workload report. A FK is expensive to
maintain; only pay for it where a rollup earns it.

**7. Counterparty tables are the back end of a form.** The reference client table had ~33
columns and vendor ~40 — almost all compliance payload (registration no., tax no., banking,
billing contact, consent). They look bloated until you realise they're filled **once, by the
counterparty, at onboarding**. Design them that way (and plan a form/intake) or they'll never
get filled. In SQLite, that's a wide `client` table populated from an onboarding form/CSV.

## Two things to improve rather than copy
- **Never hardcode tax.** The reference buried `amount*1.08` in formulas; when the rate
  changes you must hunt every one. Keep the rate in a `settings` row and reference it. Always
  ask the rate.
- **Synthetic row names depend on links being filled.** A name like
  `project || '-' || vendor || invoice_no` (a view/generated column) is good, but rows look
  broken until the FKs are set. Tell the owner that.
