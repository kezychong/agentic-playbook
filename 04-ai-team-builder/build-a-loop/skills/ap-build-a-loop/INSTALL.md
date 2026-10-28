> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

# Install — Build a Loop

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in ~/Downloads/ap-build-a-loop.zip so I can use it in every project.
```

You only need to do this once per machine. After that, it is there in every session. This works for Claude Code and Codex.

**You'll know it worked when** the agent's first move is to ask you what you make over and over again, then walks you through it **one stage at a time**, waiting for your answer before moving on. If it lectures you about theory or dumps all five stages at once, it didn't load the skill right, tell it: "one stage at a time, ask me first."

---

## Any other chat agent (can't install skills)

If your agent cannot install skills (for example, plain ChatGPT), open `references/any-agent-prompt.md` from the zip and paste it as your first message. Then say: *"build a loop with me."*

---

## What you walk away with

Whichever runtime you use, the skill writes two real files to `./loops/<loop-name>/`:

- **`loop-spec.md`** — the output you picked, its 3–5 stages, and the worker + QA-checker setup.
- **`rubric.md`** — the pass/fail checklist that encodes your taste. This is the asset that gets smarter every time you give feedback.
