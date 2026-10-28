> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

---
stage: shipped
---

# Handoff — Install & Use

A skill that writes a clean handoff document so a fresh agent, a new session, or another person can
continue your work without re-reading the whole conversation. Run it when a session is getting long,
before you clear or compact context, or when you are passing work to another machine or teammate. It
captures the goal, what is done versus still assumed, the next steps, and the files that matter, then
saves the note to a temp file and prints the path.

Works in Claude Code and in Codex. Same zip, same idea.

---

## What you need first

- The Claude app or the Codex app.
- The downloaded `ap-handoff.zip` (your agent unzips it for you).

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in ~/Downloads/ap-handoff.zip so I can use it in every project.
```

You only need to do this once per machine. After that, it is there in every session.

## Check it worked

Tell your agent:
```
/ap-handoff
```
If the skill is installed, it starts writing the handoff document. You can pass it a focus for the next
session too, for example:
```
/ap-handoff picking up the checkout bug tomorrow
```

## How to use it

1. Do your normal work until the session is getting long or you are about to switch context.
2. Run `/ap-handoff`. Add a short note of what the next session is for if you have one.
3. It writes a single handoff note: the goal, what is done versus still assumed, the next steps, the key
   files, open questions, and which skills to reach for next.
4. It saves the note to a temp file and prints the full path.
5. Open a fresh session and hand it that file. The new session picks up where you left off.

## What it will NOT do

- It will not dump the whole chat into the note. It keeps the note short and links to your plans, specs,
  commits, and issues instead of copying them.
- It will not leak secrets. API keys, passwords, and tokens get stripped out.
- It will not pretend. If something is untested, it says "assumed, not checked" rather than calling it
  done. That honesty is the whole point of a handoff.

## Why a handoff at all

Agents reason best inside a limited window. Push past it and the answers get worse, not better. Instead
of grinding on in a degraded session, you hand off: write down the state, open a clean session, and keep
the quality high. This skill makes that handoff a one-line habit.

---

*Credit where it is due: the handoff-skill pattern was popularised by Matt Pocock
(github.com/mattpocock/skills). This version is written independently.*
