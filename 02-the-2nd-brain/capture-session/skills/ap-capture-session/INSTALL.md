> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

---
stage: shipped
---

# Capture Session — Install & Use

Collection: Agentic Playbook — by Kezy. Use the included canonical skill folder.

A Claude Code skill that reads your working session and files what you learned into your vault before
you forget it. Run it at the end of a session. It finds the concepts, decisions, and insights worth
keeping, shows you the list, and after you approve it drops each one as a clean note into
`01. Inbox/agent-drops/` for your next triage to route. It is the manual Capture step of the CODE loop.

---

## What you need first

- The Claude app.
- A vault built with the Second Brain Installer (so you have `00. System/`, `01. Inbox/agent-drops/`,
  and the starter tag taxonomy). If you do not have that structure yet, run the installer first. This
  skill writes to those exact folders.
- The downloaded `ap-capture-session.zip` (your agent unzips it for you).

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in ~/Downloads/ap-capture-session.zip so I can use it in every project.
```

You only need to do this once per machine. After that, it is there in every session.

## Check it worked

Open the Claude app in your vault and tell it:
```
/ap-capture-session
```
If the skill is installed, it starts scanning the conversation. You can also just say "capture what we
learned this session" and it will trigger on its own.

## How to use it

1. Do your normal work in Claude Code (plan something, solve a problem, make a decision).
2. At the end, run `/ap-capture-session` (or "save what we learned from this chat").
3. It shows you a candidate list: the few things worth keeping, each with a proposed title and where it
   came from. Nothing is written yet.
4. Approve, cut, or edit the list. You decide what gets kept. Be ruthless. Three good notes beat twelve
   filler ones.
5. It writes the approved notes into `01. Inbox/agent-drops/`. Your next triage routes them to their
   real home and links them up.

## What it will NOT do

- It will not write anything before you approve the list. You always see it first.
- It will not file captures straight into your project folders. It drops them in `agent-drops/` on
  purpose, so your triage step does the routing. One job per step.
- It will not capture noise. Debugging, commands, and things you already saved to a file this session
  get skipped by design.
- It will not invent learnings to look busy. If the session taught nothing worth keeping, it says so.

## How this fits the bigger loop

This skill is the **manual** Capture step. The **automatic** version (a nightly process that mines every
finished session on its own) is the Memory Compaction automation already specced in your
`00. System/AUTOMATIONS.md`. Build the manual habit first. Install the automatic loop once your vault
has enough sessions to be worth mining. The manual rep is what makes the automatic version worth having.

---

*Part of the Agentic Playbook build. Fork it for your own setup by editing `SKILL.md`. If your vault uses
different folder names or tags, change the paths in the "Where captures go" and "Output format"
sections to match.*
