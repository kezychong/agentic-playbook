# Finance Agent: onboarding to a provable draft

Agentic Playbook — by Kezy

The agent's one job is to reconcile evidence, prepare reports and flag decisions for the owner.
It does not execute financial actions. Use the supplied pack in this order:

1. Read [Start Here](finance-agent/finance-agent-onboarding-pack/START-HERE.md) and complete the
   [questionnaire](finance-agent/finance-agent-onboarding-pack/onboarding-questionnaire.md) in a
   separate private draft. Record business, owner, currency, period, invoice terms, year end,
   week start and review threshold. Keep credentials out.
2. Read and sign the [money-safety agreement](finance-agent/finance-agent-onboarding-pack/money-safety-agreement.md).
   Start with manual exports. Optional [Xero](finance-agent/finance-agent-onboarding-pack/connect-xero.md)
   and [QuickBooks](finance-agent/finance-agent-onboarding-pack/connect-quickbooks.md) guides describe
   future approval-gated read access; they do not install or connect anything.
3. Stage the [distribution templates](finance-agent/finance-agent-distribution/README.md) in a
   separate folder. Fill placeholders consistently. SOUL is identity; AGENTS/HERMES are the operating
   manual; YAML is an unverified schema template; env-example.txt contains key names only; MCP is empty.
4. Run the [readiness checklist](finance-agent/finance-agent-onboarding-pack/go-live-checklist.md)
   with supplied files: correct entity, exact invoice fields, bank proof, P&L basis, settings,
   safety boundaries and no unexpected schedules. Checklist success never unlocks ledger writes.
5. Use [Weekly Money Report](finance-agent/skills/ap-weekly-money-report/SKILL.md) for one fixed report shape.
   Use [Monthly Close](finance-agent/skills/ap-monthly-close/SKILL.md) for seven confirmations: entity/period,
   complete statements, reconciliation, invoices/credit notes, bills, comparative drafts, final filing.
   Filing means saving a local report, not a government submission or changing the accounting period.

For each figure record source, period, currency and actual/forecast/pending/disputed status.
Paid invoice status alone is not cash: inspect credit notes and match the deposit. P&L requires
ledger/accrual evidence, not merely bank movements. Missing prior periods mean “comparison unavailable.”
When prior value is zero, show absolute change and mark percentage change undefined.

## Routines and approval
Nothing runs automatically. A future schedule proposal must include frequency, timezone, approved
sources, cost, output destination, human reviewer and pause procedure. Approval to report is not
approval to send reports elsewhere. No payments, trades, filings, payroll or production ledger writes.

## Update and removal
Compare template changes in a staged copy and review filled placeholders privately. Never overwrite
an existing finance profile or manual. For removal, pause separately created schedules, revoke any
connector, verify access is gone, then remove only approved installed files. Decide export retention
separately. These steps are guidance; no live installation or connection has been tested.
