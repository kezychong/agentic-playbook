> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

---
stage: shipped
---

# Voice Recognition — Install & Use

Collection: Agentic Playbook — by Kezy. Use the included canonical skill folder.

A skill that compares a speaker's voice sample against a set of saved, human-approved voice profiles
and reports the closest match, or that none was found. It never guesses a name from context, and it
never auto-applies a result; every match is held for human confirmation.

---

## What you need first

- The Claude app (or compatible host).
- At least one saved voice profile, created and confirmed by a human from a sample they personally
  verified. This skill does not ship any profiles.
- A voice sample to check, from a recording or audio clip.
- The downloaded `ap-voice-recognition.zip` (your agent unzips it for you).

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in ~/Downloads/ap-voice-recognition.zip so I can use it in every project.
```

You only need to do this once per machine. After that, it is there in every session.

## Check it worked

Open your agent and tell it:
```
/ap-voice-recognition
```
If the skill is installed, it asks for the voice sample and the saved profiles to compare it against.

## How to use it

1. Create and confirm at least one voice profile first (see `SKILL.md`'s Profile format). This is a
   one-time step per person, done by a human, not by this skill.
2. Give it a voice sample to check.
3. It compares the sample to every saved profile and reports either a candidate match with its
   confidence score, or "no confident match."
4. You confirm (`yes`), reject (`no`), or correct (`change: <value>`) the result. Nothing downstream
   treats the match as settled until you answer.

## What it will NOT do

- It will not identify an unregistered or unknown voice.
- It will not infer a speaker's name from the words said, tone, or context. Only a saved profile match
  or your own direct identification counts.
- It will not create or approve a voice profile on its own.
- It will not write a confirmed name into a transcript or note without your explicit confirmation.

## How this fits a meeting workflow

This skill pairs with the optional `ap-meeting-intelligence` package: it can resolve a speaker row that
skill's review queue flagged as unclear. It is not required for that package to work, and does nothing
on its own without a human-approved profile set in place.

---

*Part of the Agentic Playbook build. Fork it for your own setup by editing `SKILL.md`. If your profile
storage uses a different location, change `{{VOICE_PROFILES_PATH}}` to match.*
