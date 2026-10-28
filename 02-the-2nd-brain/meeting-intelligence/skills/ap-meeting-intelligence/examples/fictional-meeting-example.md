# Fictional walkthrough: a recorded planning meeting

Agentic Playbook — by Kezy · Fictional sample, not an executed test

## Input (fictional transcript excerpt)

A 12-minute recorded planning call between two fictional teammates at a fictional company, "Acme Co."
The recorder app's export gives generic speaker labels.

> Speaker 1: Morning. Quick sync on the Acme sync tool rollout.
> Speaker 2: Sounds good. I think budget is $5k for this quarter.
> Speaker 1: Right, and Alex is going to own the rollout checklist, due next Friday.
> Speaker 2: Actually hold on, I said budget is $8k earlier, didn't I?
> Speaker 1: We should ship the pilot by Friday. Priya, can you draft the announcement?
> Speaker 2: Sure, I'll draft it.

## Drafted minutes (held, not yet confirmed)

**Summary:** Acme Co.'s team planned the pilot rollout of a sync tool, discussed budget, and assigned
two follow-up tasks.

**Decisions:** Ship the pilot by Friday.

**Action items:**
- Rollout checklist — owner: Alex — due: next Friday
- Draft announcement — owner: Priya (unconfirmed — line attributed to "Speaker 2") — due: none given

**Follow-ups:** Confirm final budget figure.

## Review queue raised

| # | Type | Quote / line | Question | Best guess | Decision |
|---|------|--------------|----------|------------|----------|
| 1 | speaker | "Sure, I'll draft it." | Is this line really Priya (Speaker 2)? | Priya, unconfirmed | |
| 2 | term | "the Acme sync tool" | Is "Acme sync" the correct product name? | Acme Sync, not in glossary | |
| 3 | contradiction | "budget is $5k" vs "I said budget is $8k earlier" | Which figure is correct? | unresolved | |

## Human answers (fictional)

1. `change: Priya` — confirmed, not Speaker 2 generically; the human knows Priya was on the call.
2. `change: AcmeSync` — correct product name is written as one word, per the human.
3. `change: $8k` — the $8k figure is correct; $5k was an earlier draft number.

## Confirmed minutes (after approval)

```markdown
# Meeting minutes — Acme Co. pilot rollout sync, 2026-10-04

captured: 2026-10-04
source: fictional recorder export, planning call
status: confirmed

## Summary
Acme Co.'s team planned the pilot rollout of AcmeSync, confirmed an $8k quarterly budget, and assigned
two follow-up tasks.

## Decisions
- Ship the pilot by Friday — reasoning: team agreed in the call.

## Action items
- [ ] Rollout checklist — owner: Alex — due: next Friday
- [ ] Draft announcement — owner: Priya — due: none given

## Follow-ups
- None remaining; budget figure confirmed at $8k.

## Notes still held
- None.
```

## Glossary updated

```markdown
- "Acme sync tool" → "AcmeSync" (confirmed 2026-10-04, review queue #2)
```

## Negative check

If the human had answered row 1 with `later` instead, "Draft announcement" would stay attributed
generically ("Speaker 2, unconfirmed") in the confirmed notes, and the row would remain open in the
held queue for the next pass. The skill does not promote a guess to confirmed just because time
passed.

<!-- Agentic Playbook — by Kezy -->
