---
name: ap-fusion-council
description: "Run a hard decision past several different models answering separately, anonymise the answers, and judge one decision memo with receipts. Use for \"run a fusion council on this\", \"get a council on this decision\" or \"pressure-test this choice\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Original starter method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Fusion Council

Use for decisions where a blind spot is expensive: a hire, a price change, a strategy fork, a risky technical choice. Not for quick, low-stakes questions.

## 1. Frame the question

Write one brief that every seat receives word for word: the decision, the options known so far, the constraints, what a good answer must include (recommendation, reasons, risks, what would change the answer). Show the brief to the owner and adjust it once.

## 2. Pick the seats

Use 3 to 5 seats from **different model families** the host can actually call today (for example one each from different labs, through their CLIs, subagents or API routes the owner already pays for). Diversity beats size: two copies of the same model is one opinion. List the seats and their cost class to the owner before running; paid calls need approval.

## 3. Seal each seat

Run every seat in a fresh session with only the brief. No seat sees another's answer. Save each answer to its own file.

## 4. Strip the names

Relabel the answers A, B, C... and remove any model self-reference, so the judge weighs reasoning, not reputation.

## 5. Judge

As the judge (the strongest model available, in a fresh context), read all answers and write one decision memo:
- **Verdict** in one line, and how confident.
- **Where the seats agreed** (likely solid) and **where they split** (the real decision).
- **The strongest point from each seat** that survived, and anything every seat missed.
- **What would change the verdict**, and the cheapest test to check it.

## 6. Receipt

End with which seats ran, which answer each surviving point came from, and anything that failed or timed out. Never claim a seat ran if it did not.

<!-- Agentic Playbook — by Kezy -->
