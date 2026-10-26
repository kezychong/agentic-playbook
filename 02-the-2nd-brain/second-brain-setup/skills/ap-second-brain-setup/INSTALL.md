> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

# Install: Second Brain Setup

This skill builds your AI second brain for you: the folders, the rules, and four helper skills your agent keeps forever. You install it once, then just talk to your agent.

## What you need

- A Mac with the Claude app or Claude Code already working.
- The file `ap-second-brain-setup.zip` (this download), saved in your Downloads folder.
- Your exports (ChatGPT, Claude, business documents) saved somewhere on this Mac. Already dumped inside your second-brain folder? Also fine. The agent will tuck the raw originals into a safe holding folder during setup and bring the organized notes back in.

## Install manually after review

1. Make a fresh folder for your second brain if you don't have one yet. `Documents/second-brain` is perfect.
2. Open your agent in that folder.
3. Say this to your agent:

> There's a file called ap-second-brain-setup.zip in my Downloads folder. Unzip it and install the skill inside it into this folder's skills, then read it and tell me you're ready.

That's it. The agent will place the skill where it belongs and confirm.

## For the agent doing the install

- Select the complete `ap-second-brain-setup/` folder plus the four sibling folders `ap-distill/`, `ap-triage-inbox/`, `ap-import-ai-exports/` and `ap-weekly-sweep/`. Keep this dependency group together.
- Move that whole folder to `.claude/skills/ap-second-brain-setup/` inside the current vault folder (create `.claude/skills/` if it doesn't exist). Move it in one step, don't copy-then-delete.
- Verify `SKILL.md` and `templates/` in setup, and verify SKILL.md in each of the four canonical sibling helper folders. There is no nested vault-skills directory in this repackage.
- Then read `SKILL.md` and tell the user you're ready to start with Phase 0.

## Start the setup

When the agent says it's ready, say:

> Set up my second brain.

The agent will check it's in the right folder, build everything, and walk you through it one question at a time. You can stop anytime and pick it up later, nothing breaks.

## After setup, your four everyday phrases

- "**Triage my inbox**": sorts whatever you've dropped in.
- "**Distill this**": pulls the lasting ideas out of a big document.
- "**Import my exports**": brings in new ChatGPT or Claude conversations.
- "**Weekly sweep**": the once-a-week health report.

## Already have a second brain from the old installer?

Same install, no extra steps. Just open the Claude app inside your existing second brain folder instead of an empty one, and hand it the same file. It will recognize your setup and upgrade it in place, adding the new machinery around what you already have. It will not delete or rewrite a single note you've written.

Agentic Playbook — by Kezy
