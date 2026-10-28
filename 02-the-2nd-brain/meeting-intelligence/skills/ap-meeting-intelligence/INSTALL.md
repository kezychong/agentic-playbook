> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

---
stage: shipped
---

# Meeting Intelligence — Install & Use

Collection: Agentic Playbook — by Kezy. Use the included canonical skill folder.

A skill that reads a meeting recording or transcript and turns it into minutes: a summary, decisions,
action items with owners, and follow-ups. Anything it is not confident about (a speaker, a term's
spelling, a contradiction) goes into a short review queue first. You answer each row yes, no, change,
or later; only confirmed items reach the final notes.

---

## What you need first

- The Claude app (or compatible host).
- A transcript, or a recording the host can transcribe, from any voice recorder app's export.
- A notes/inbox location to write minutes into. If you do not have one, point the skill at a plain
  folder; it does not require a specific second-brain structure.
- The downloaded `ap-meeting-intelligence.zip` (your agent unzips it for you).

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in ~/Downloads/ap-meeting-intelligence.zip so I can use it in every project.
```

You only need to do this once per machine. After that, it is there in every session.

## Check it worked

Open your agent and tell it:
```
/ap-meeting-intelligence
```
If the skill is installed, it asks for the transcript or recording. You can also just say "turn this
meeting recording into minutes" and it will trigger on its own.

## How to use it

1. Give it a transcript or recording (paste it, point to a file, or hand over a recorder export).
2. It drafts the minutes and a short review queue for anything unclear: unclear speaker attribution,
   unclear terms or spellings, or statements that contradict each other.
3. It shows you the queue, one line per item. Answer each one `yes`, `no`, `change: <value>`, or
   `later`. Nothing is written to your final notes until you answer.
4. It writes the confirmed minutes to your notes location. Corrected terms are saved to a small
   glossary, but only the ones you explicitly confirmed.
5. Anything left `later` stays in the held queue for next time.

## What it will NOT do

- It will not guess who is speaking from the words alone. It uses existing speaker labels and flags
  the rest; identifying a voice from a saved profile is the separate, optional `ap-voice-recognition`
  companion.
- It will not write an uncertain name, term, decision, or action item into your notes without your
  explicit answer on that row.
- It will not auto-replace a term anywhere else just because you corrected it once. Confirmed terms
  are applied going forward only, and only added to the glossary after your confirmation.

## How this fits a notes workflow

This skill produces minutes and a review queue; it does not require a particular vault layout. If you
use the Agentic Playbook second-brain packages, point `{{MEETINGS_FOLDER}}` and `{{NOTES_INBOX}}` at
your existing Inbox/Projects structure instead of a plain folder.

---

*Part of the Agentic Playbook build. Fork it for your own setup by editing `SKILL.md`. If your notes
use different folder names, change the paths in the "Runtime path conventions" section to match.*
