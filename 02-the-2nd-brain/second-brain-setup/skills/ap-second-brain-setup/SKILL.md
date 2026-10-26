---
name: ap-second-brain-setup
description: "Build or upgrade a PARA vault with receipts."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Second Brain Setup

You are setting up a second brain: one folder of plain markdown notes, readable in Obsidian, operated by you (the agent). The owner decides, you do the moving.

This skill knows nothing about the owner's businesses until you ask. The interview in Phase 1 shapes the vault around their real work. Never assume what they do; ask, then build.

## How to behave

- The user is a business owner, not a technical person. Plain English. Short sentences. No tech words: say folder, file, app, agent. If a technical term is unavoidable, explain it in one short sentence.
- One question at a time. Never stack questions. Always offer a default so every question is easy to answer.
- Confirm before writing anything in Phase 0 and Phase 1. After that, work in batches and show receipts.
- Match the owner's language. If they answer in another language, accept it.
- Safe to stop at any point. When re-run, do the resume check at the bottom instead of starting over.

## Ground rules (never break these)

1. **Privacy gate.** Bulk message archives (Telegram, WhatsApp, Slack, or similar exports), client personal data, account numbers, contracts, bank or brokerage statements, IDs and tax documents NEVER enter the vault. Raw exports stay in a read-only "Source Mirror" folder outside the vault. Only converted notes and light indexes come in.
2. **Receipts.** Every file move appends one row to `01. Inbox/WHERE-DID-IT-GO.md`. No silent moves.
3. **Never delete.** Nothing is deleted or overwritten without the owner's word. Old things go to `05. Archives/`.
4. **Move directly.** Move files in one step. Never copy a file and then delete the original.
5. **AI memory is not truth.** Claims from ChatGPT or Claude memory summaries stay unverified until the owner confirms them.
6. **Unsure means ask.** Never guess where something goes.

## Phase 0: Safety checks (before anything)

1. Confirm you are inside the folder that will become the second brain. Show the user the folder path and ask "this is where I'll build, right?"
2. If the path is a top-level place (Desktop itself, Documents itself, the home folder) suggest making a fresh folder like `Documents/second-brain` and building there.
3. If the path contains iCloud, Google Drive, Dropbox or OneDrive, warn once: live-sync folders fight with live editing and cause duplicates. Offer to use a normal local folder instead. The user may still choose to continue.
4. List what is already in the folder. Work around existing files, never over them.
5. Check for signs of a second brain already built by the old Agentic Playbook installer: a `00. System/` folder, a root `CLAUDE.md` whose first line contains "Operating Manual for", or a `05. Archive/` folder (singular, not plural). If you see any of these, do not build fresh. Jump straight to "Upgrade mode: brains built by the old installer" below.

## Phase 1: Interview, then build the vault

### 1a. Lay the base

1. Copy everything inside this skill's `templates/vault/` folder into the vault root. That creates the five PARA folders plus `_System/`, the operating manual (`AGENTS.md`), the Inbox contract, the routing map, tags, and note templates. No business folders exist yet; the interview builds those.
2. Read the new `AGENTS.md` and `_System/VAULT_MANIFEST.md` so you know the rules you just installed.

### 1b. The interview (one question at a time)

1. **Name.** "What's your first name?" Then replace every `[Owner]` placeholder in the copied template files with it (search the whole vault for `[Owner]` so none survive). If they'd rather not say, use "the owner" and still clear the placeholders.
2. **Businesses.** "Tell me about each business or income stream you run: its name, plus one sentence on what it does and who helps you run it. Most people have 1 to 3." If they hesitate, offer to start with one folder called `My Business (rename me)` they can rename later.
3. **Shelves.** For each business, read this skill's `templates/business-area/SHELF-MENU.md` and propose 3 to 7 shelves that fit what the owner just told you. Read the proposal out loud, one business at a time, and adjust until it sounds like their business. Custom shelf names are welcome; the menu is a starting point, not a limit.
4. **Projects (optional).** "Any active projects with a real finish line, like a launch or a one-off client job, that you want folders for now?" Default: none. Projects can be created later as work arrives.

### 1c. Build from the answers

1. Create one folder per business in `03. Areas/`, named exactly what the owner calls it. Inside each, create the agreed shelves. Write each business folder's `README.md` from this skill's `templates/business-area/README-template.md`, filled with what the owner said, and give each shelf a `README.md` of one or two plain sentences saying what belongs on it.
2. Add one business tag per business to `_System/TAG_TAXONOMY.md` under "Business tags", using a short lowercase word from the business name (for example `#biz/gym`). Confirm each tag with the owner.
3. Create any project folders from the interview in `02. Projects/`, each with a short `STATUS.md`.
4. Update the folder tree in `_System/VAULT_MANIFEST.md` so it lists the real business folders and their shelves. The manifest must match what exists, always.

### 1d. Boundaries

1. Ask where the raw exports live (the Source Mirror). Write that location into `_System/VAULT_MANIFEST.md` under "Source Mirror location". If the raw exports are currently INSIDE the vault folder, move them out to the Source Mirror first, with the owner's OK.
2. Ask what is off-limits beyond the default privacy gate, and note any additions in the manifest.
3. Finish with a sweep: search the whole vault for `[Owner]` and `(rename me)`. Nothing should remain unless the owner deliberately kept a placeholder business name.

## Phase 2: Install the helper skills

1. After approval, copy the four complete sibling folders `../ap-import-ai-exports/`, `../ap-triage-inbox/`, `../ap-distill/` and `../ap-weekly-sweep/` into the vault's `.claude/skills/` folder (or the documented skill location of the chosen host). That installs four skills the owner keeps forever:
   - **ap-import-ai-exports**: turns ChatGPT and Claude exports into one tidy note per conversation plus a master index.
   - **ap-triage-inbox**: sorts whatever is sitting in `01. Inbox/` into the right home, with receipts.
   - **ap-distill**: pulls the lasting ideas out of a big document into small notes that stand on their own.
   - **ap-weekly-sweep**: a weekly health check that reports and proposes, never moves things itself.
2. Confirm the four skill folders exist in the vault, then tell the owner in one line each what they can now ask for.

## Phase 3: Import the AI exports

Run the **ap-import-ai-exports** skill on the ChatGPT export and the Claude export in the Source Mirror. It works in batches and logs progress, so it can be stopped and resumed. When it finishes, show the owner the index and the ten most valuable conversations it found.

## Phase 4: Bring in the business documents

The Source Mirror usually holds business documents too. Ask the owner:

> "Which documents would a new team member need on day one? Think playbooks, offer or price sheets, step-by-step process docs, pitch decks. Aim for 3 to 7. Name them and tell me where they live."

For each one:

1. Check it against the privacy gate first. Anything with account numbers, client personal data, or contract terms stays in the Source Mirror and is only pointed at, never copied in.
2. Convert the safe ones into a markdown note on the right shelf. Say the destination out loud before converting: "the pricing deck goes on [Business]'s Offer & Economics shelf, agreed?"
3. The original file stays in the Source Mirror untouched. The note names its original file so it can always be traced back.
4. Every note created this way gets a receipt row in `01. Inbox/WHERE-DID-IT-GO.md`.
5. If the owner names a document they can't find, note it as missing in that business folder's README so it stays visible instead of being forgotten.

## Phase 5: First sorting pass

Run the **ap-triage-inbox** skill. For a first pass this size, it will classify everything first and show a proposal (item, destination, one-line why) before moving anything. Get the owner's OK, move, show receipts.

## Phase 6: Distill the gold

Run the **ap-distill** skill on the most valuable documents first, now that Phase 4 filed them on their shelves. Ask the owner: "If you could only keep three of these documents, which three?" Distill those first, in their order.

Then continue with whatever the import index flagged as most valuable.

## Phase 7: Hand over the loop

Teach the owner the daily habit, in three sentences:

> Drop anything new into `01. Inbox/`, messy is fine. Ask me to "triage my inbox" whenever it piles up, and "ap-distill" anything meaty. Once a week ask for the "weekly sweep" and I'll tell you the state of the whole brain.

Offer a weekly reminder; agree the day, time, timezone and scope, and obtain explicit approval before creating a schedule.

Autopilot scheduling packs mentioned in the original method are not included. Run these skills manually. If the owner later approves a host scheduler, document the real vault paths, timezone, cost, permissions and disable procedure before activating it.

## Upgrade mode: brains built by the old installer

1. Open by telling the owner what you found, close to this: "You already have a working second brain from the old installer. I'll upgrade it in place. Every note you have stays exactly where it is. I only add the new machinery."
2. Harvest, don't re-ask. Read their existing root `CLAUDE.md`. Their name, what they do, their style, their projects, and their areas are already written in there. Carry all of it over, never re-interview them for it. Only ask what the old brain can't answer:
   - The businesses and shelves questions from Phase 1b, and only if their `03. Areas/` folders are generic life areas rather than named businesses. Even then, ask first whether they want business folders added at all. Default: keep what they have.
   - Where the raw exports live (the Source Mirror).
   - Anything extra that's off-limits beyond the default privacy gate.
3. Check for running schedules first, before touching any folder name. Look for signs of installed autopilot jobs: a `00. System/INSTALLED-PACKS.md` file listing autopilot packs, a `~/.vault-cron/` folder, or scheduler entries whose names mention the vault or vault-cron. If you find any of these, tell the owner plainly: "You have scheduled jobs that read files inside `00. System/`. If I rename that folder, those jobs quietly break." In that case the default flips: keep the old folder names, record them in `_System/VAULT_MANIFEST.md` (or their existing system folder), and skip the renames below. Only rename if the owner asks for it, and then update every path those jobs read in the same sitting (the wrapper scripts in `~/.vault-cron/`, the prompt file, the feedback file), and run one supervised test of each job before calling it done. Every change gets a receipt row.
4. Only after the schedule check above, and only with a one-word OK each: two folder renames, `00. System` becomes `_System`, and `05. Archive` becomes `05. Archives`. Move each folder in one step, a direct rename, never copy-then-delete. If the owner would rather keep the old names, that's fine too. Keep them, and write the real names into `_System/VAULT_MANIFEST.md` (or their existing system folder) so every skill knows where things actually live.
5. Add what's missing, never overwrite what exists. Copy in from this skill's `templates/vault/` only the files their brain doesn't already have: the receipts ledger `01. Inbox/WHERE-DID-IT-GO.md`, `_System/VAULT_MANIFEST.md`, `_System/templates/` note templates, and `_System/LINKING_RULES.md` only if it's missing. For `_System/TAG_TAXONOMY.md`, merge instead of replace: keep every tag the owner already has, add only the new sections that are missing, and never delete their tags.
6. Build the new root `AGENTS.md` from the template, filled with the name, projects, areas, and style you harvested from their old `CLAUDE.md`. Then replace the old `CLAUDE.md` content with a one-line pointer to `AGENTS.md`, but only after you've confirmed everything personal from it now lives in `AGENTS.md`. Nothing from their old manual gets lost.
7. Every rename and every file you add gets a receipt row in `01. Inbox/WHERE-DID-IT-GO.md`. These become the first rows of their new ledger.
8. Then continue at Phase 2 (install the four helper skills), and run Phases 3 to 7 as they apply. Skip Phase 3 if they have no AI exports to import. Phase 5 (first triage) is usually the biggest win for an existing brain. Finish with Phase 7 and the weekly rhythm.
9. Starter ap-distill pass (recommended). An upgraded brain usually has months of notes and nothing distilled, and the weekly rhythm alone would take months to catch up. Offer a one-time catch-up: after the first triage, list the 10 most valuable un-distilled notes (use the import index if there is one, what the owner points at, and what other notes reference most). The owner trims or reorders the list. Distill them in batches of 5 with the ap-distill skill, showing receipts after each batch, stopping whenever the owner says stop. Leftovers carry to the next session, not to a schedule. One or two sittings of this is what makes the upgrade feel different in the first week: the agent starts finding the right note on the first try.
10. Safety line, always true in upgrade mode: never delete a note, never rewrite the owner's own writing, and anything unclear gets asked, not guessed.

## Definition of done

- [ ] PARA folders + `_System/` exist; one folder per business in `03. Areas/`, named what the owner calls it, with agreed shelves and READMEs
- [ ] No `[Owner]` or unwanted `(rename me)` placeholders left anywhere
- [ ] One `#biz/` tag per business in `_System/TAG_TAXONOMY.md`
- [ ] Source Mirror location recorded in the manifest
- [ ] Four helper skills installed in the vault's `.claude/skills/`
- [ ] Both AI exports imported, `01. Inbox/exports/INDEX.md` built
- [ ] Key business documents converted onto their shelves, originals untouched in the Source Mirror
- [ ] First triage done, receipts written
- [ ] Top 3 documents distilled
- [ ] Owner has dropped one test file into Inbox and watched it get routed
- [ ] If upgrading an old-installer brain: renames confirmed or declined-and-recorded, missing system files added, `AGENTS.md` carries the owner's old manual content, receipts written, and zero notes lost
- [ ] Schedule check run before any rename; no scheduled job left broken by the upgrade

## Resume check (when re-run)

Run these checks in order and jump to the first phase that is not done:
1. Old-installer brain detected (the Phase 0 step 5 signs) and no `_System/VAULT_MANIFEST.md` (or no recorded upgrade) yet? → Upgrade mode.
2. Vault folders exist, at least one business folder in `03. Areas/` with shelves, no `[Owner]` placeholders left, and the Source Mirror location recorded in the manifest? If any of those are missing → Phase 1.
3. Four helper skills inside the vault's `.claude/skills/`? If not → Phase 2.
4. `01. Inbox/exports/INDEX.md` exists and matches the export counts? If not → Phase 3 (it resumes from existing files).
5. Business documents present on their shelves? If not → Phase 4.
6. Inbox has unrouted items? → Phase 5.
7. Gold documents marked `status: distilled`? If not → Phase 6.
8. Otherwise → Phase 7 refresh, then run a weekly sweep.
