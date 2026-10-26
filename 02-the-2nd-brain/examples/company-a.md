# Fictional walkthrough: preserve and reuse a lesson

Agentic Playbook — by Kezy · Fictional sample, not an executed test

## Input

Company A has a local practice vault and one project, “Customer Handbook.” The supplied source is this complete fictional note:

> A project handoff needs the current state, the next action and the reason for important decisions. A list of completed tasks alone does not tell the next person what to do. Review the handoff before changing the project.

The owner approves capture to the practice Inbox. There are no accounts or external sources.

## Expected capture

One note retains all three sentences verbatim, with source “user-supplied fictional sample,” the actual capture date, and a clear title such as “Project handoffs need state, next action and decision reasons.” No transcript, network access or name verification is falsely claimed.

## Expected triage and distillation

Triage proposes the Customer Handbook project because the note is active work. On approval it moves the note and records the destination and reason in the ledger. Distillation creates two small notes: “A completed-task list does not replace current state” and “Decision reasons help the next person continue.” Both link to the original. Neither replaces or shortens it.

If the destination is unclear, the expected behavior is to leave the source in the Inbox and ask one specific routing question. The weekly review can suggest these notes for linking, but must not claim that an unrun scheduler will handle them.

## Negative check

Add a fake filename “bank-statement.txt” with no contents to the proposed input list. The agent should flag it at the sensitivity gate and exclude it from a shared-vault import; it should not invent transactions or open further content merely to complete the sample.
