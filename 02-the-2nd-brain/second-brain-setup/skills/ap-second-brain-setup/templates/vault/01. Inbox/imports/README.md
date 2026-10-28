---
type: reference
status: organized
source: system
created: 2026-07-24
---

# Imports Staging: converted AI conversations land here first

This folder is a waiting room, not a home. When the `ap-import-ai-exports` skill runs, it turns raw ChatGPT and Claude conversation exports into one clean note per conversation, plus one `INDEX.md` that lists them all.

Converted notes land in two folders:
- `converted/chatgpt/`: one note per ChatGPT conversation
- `converted/claude/`: one note per Claude conversation

Every note starts tagged `#status/inbox`, because nobody has looked at it yet.

From here, the `ap-triage-inbox` skill (or the owner, by hand) decides what happens to each note:
- Worth keeping as general reference: goes to `04. Resources/AI Conversations/`
- Specific to one business: goes to that business's shelf in `03. Areas/`
- Not worth keeping: goes to `05. Archives/`

Raw export files (the original ChatGPT or Claude download, and any attachments) never live here and never enter the vault at all. They stay in the read-only Source Mirror folder outside the vault. Only the converted, cleaned-up notes come in.
