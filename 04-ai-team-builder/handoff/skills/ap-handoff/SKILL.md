---
name: ap-handoff
description: "Write a self-contained handoff (goal, verified vs assumed state, next steps, key files, open questions) so a fresh session or another agent can continue cold. Use at the end of a long session, before clearing context, or when passing work on."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Handoff

## Who This Is For

The member using this skill is a smart business owner, not a technical person. They work inside the Claude app or the Codex app and never open a terminal.

The agent reading this skill does all the writing itself: pulling together the state, saving the document, and reporting back where it lives. Narrate this in plain words. Never ask the member to open a file path or run anything themselves.

You are closing one working session and setting up the next one. Produce a single, self-contained handoff document so a fresh agent, a new context window, or another person can pick the work up cold and keep going, without re-reading this entire conversation.

Write for a reader who was not here. Assume zero shared memory. Keep it short enough to read in a minute.

## Where to save it

Write the document to the operating system's temporary directory, not the working folder, so it does not clutter the project or get committed by accident. Print the full path at the end so it is easy to open. If the user named a folder, use that instead.

## What to include

1. **Goal** — the outcome we are driving toward, and what "done" looks like, in a line or two.
2. **Current state** — what is finished, what is half-done, what is blocked. Keep two things separate: what has been **verified** (run, tested, seen working) and what is still **assumed** (looks right, not yet checked). Label which is which. This is the single most useful thing in a handoff.
3. **Next steps** — the concrete actions the next session should take, in order. Lead with the very first thing to do.
4. **Key files and locations** — the paths, URLs, branches, or commands that matter, so the next session knows where to look.
5. **Open questions** — anything unresolved that needs a decision, with the options if you know them.
6. **Suggested skills or tools** — name the skills, commands, or tools the next session should reach for, so it does not have to rediscover them.

## Rules

- **Point, do not copy.** If a plan, spec, PRD, issue, commit, or diff already holds the detail, link to it by path or URL instead of pasting it back in. The handoff points to the truth; it does not duplicate it. If your document is getting long, you are probably copying something that should be a link.
- **Redact secrets.** Strip API keys, passwords, tokens, and personal information. If a value is needed, say where it lives ("in the `.env` file"), not what it is.
- **Be honest about state.** "The test is failing and I do not know why yet" is more useful than a tidy summary that hides it. Never dress up an assumption as a fact.
- **Tailor to the purpose.** If the user passed a note about what the next session is for, shape the whole document around that focus and cut anything off-topic.

## Template

```
# Handoff: <short title>
Date: <date>    For: <what the next session will focus on>

## Goal
<the outcome, and what "done" looks like>

## Current state
Done:
- ...
In progress:
- ...
Blocked / needs a decision:
- ...

Verified vs assumed:
- Verified (seen working): ...
- Assumed (not yet checked): ...

## Next steps
1. <the first thing to do>
2. ...

## Key files & locations
- <path or URL> — <why it matters>

## Open questions
- <question> — <options, if known>

## Suggested skills / tools
- <skill or command> — <when to use it>

## Reference (do not duplicate)
- <link to the plan / spec / issue / commit that holds the detail>
```

When you finish, save the file, then print its full path so it can be opened in the next session.

---

*The handoff-skill pattern was popularised by Matt Pocock (github.com/mattpocock/skills). This version was written from scratch.*

<!-- Agentic Playbook — by Kezy -->
