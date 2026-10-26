---
type: reference
status: organized
source: system
created: 2026-07-24
---

# Vault Manifest: the map of this second brain

Read this before you move, create, or remove anything. Created a folder or removed one? Update this file in the same change. This file is the source of truth for where things live.

## Folder tree

- `01. Inbox/`: landing zone for anything new. Nothing stays here long. See its `README.md` for the routing rule.
  - `01. Inbox/exports/`: converted AI conversations wait here before triage. See its `README.md`.
- `02. Projects/`: things the owner is actively working on, each in its own folder, each with a clear finish line.
  - `02. Projects/Second Brain Setup/`: the starter project for getting this whole system running.
- `03. Areas/`: the businesses and personal life, always on, no finish line.
  - One folder per business, created on setup day from the Phase 1 interview. List each business folder and its shelves here as they are created, like this:
  - `03. Areas/[Business Name]/`, shelves: [list the shelves].
  - `03. Areas/Personal/`: health, family, and personal admin.
- `04. Resources/`: reference material that isn't tied to one business.
  - `04. Resources/Playbooks/`: general playbooks, not specific to one business.
  - `04. Resources/AI Conversations/`: kept AI conversations worth referencing later.
- `05. Archives/`: anything finished, expired, or no longer useful, kept but out of the way.
- `_System/`: the rules and templates that keep this vault consistent (this file, tags, linking rules, note templates).
- `.claude/skills/`: the agent skills installed in this vault: `ap-second-brain-setup` (the one-time setup skill) plus the four everyday skills, `ap-import-ai-exports`, `ap-triage-inbox`, `ap-distill`, `ap-weekly-sweep`.

## Routing rules

| Kind of content | Goes to |
|---|---|
| Active plan, draft, or idea the owner is still working on | `02. Projects/<matching project>/` |
| Business document (no account numbers, no personal data) | The matching shelf in `03. Areas/<business>/` |
| General reference, article, or swipe file | `04. Resources/` |
| Playbook specific to one business | That business's shelf in `03. Areas/` |
| Playbook that applies to every business | `04. Resources/Playbooks/` |
| AI conversation worth keeping | `04. Resources/AI Conversations/` (or a business shelf if it's specific to one) |
| Junk, expired, or superseded material | `05. Archives/` |
| Sensitive documents (see Privacy gate below) | Never routed. Flag to the owner, leave it in place. |

If nothing above fits, leave it in `01. Inbox/`, tag `#status/inbox`, and ask the owner.

## Privacy gate: what never enters this vault

These never get copied, converted, or filed into any vault folder, no exceptions:
- Bulk message archives (a full Telegram, WhatsApp, Slack, or similar message history export)
- Any client's personal details: names tied to ID numbers, addresses, phone numbers, health or financial details
- Bank or brokerage statements
- Contracts
- Tax documents
- Anything carrying a government ID, passport, or license number

Anything the owner adds to this list during setup day gets written here too.

The vault can still hold a light index: a short note that says this material exists, what it's about, and where to find it. That index points to the restricted material sitting in the Source Mirror. The index itself must never contain the restricted content, only a description and a pointer.

## Source Mirror location

The Source Mirror is the read-only folder outside this vault that holds every raw export and every restricted document. Fill in its location here on setup day:

`Source Mirror location: [fill in on setup day]`

## Keeping this file honest

Created a folder, removed one, or renamed a business folder? Update this manifest in the same change, not later.
