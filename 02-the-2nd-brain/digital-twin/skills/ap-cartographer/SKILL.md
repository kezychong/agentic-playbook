---
name: ap-cartographer
description: "Scan the atomic notes Digital Twin extracted, detect recurring work domains, and for each one let the owner create an Area, attach a subfolder, rename or skip, then re-route the notes. Use for \"map my work domains\" or \"run the cartographer\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Cartographer

You are installing THE CARTOGRAPHER.

This pack EXTENDS Digital Twin. Digital Twin captured WHO you are — voice, values, mental models, goals. Cartographer captures WHAT YOU DO — by scanning the atomic notes Digital Twin already extracted from your chat history and detecting recurring WORK DOMAINS (copywriting, investment analysis, presentations, code, marketing, etc.).

For each detected domain, the user decides: create as a new Area, attach as a subfolder under an existing Area, rename, or skip. The pack then builds the folder structure and re-routes the relevant atomic notes into their proper home.

Phases:
  Phase 0  Pre-flight — require Second Brain Setup + Digital Twin installed
  Phase 1  Scan atomic notes for work-domain clusters
  Phase 2  Interactive review — confirm/rename/subfolder/skip per domain
  Phase 3  Create Area / subfolder structure
  Phase 4  Re-route atomic notes into the new homes
  Phase 5  Cross-reference back into 03. Areas/Self/digital-twin/
  Phase 6  Register pack in _System/INSTALLED-PACKS.md
  Phase 7  Closeout

CRITICAL DESIGN: every phase persists progress to disk before moving on. The user can quit anytime and resume by saying "continue" in a new Claude Code session — same resume mechanic as Digital Twin.

Read this whole prompt before doing anything. Don't run anything until I say "go."

═══════════════════════════════════════════════════════════
PHASE 0 — PRE-FLIGHT
═══════════════════════════════════════════════════════════

1. Confirm vault root. Verify the following exist:
   - `CLAUDE.md` (root operating manual)
   - `_System/` with system files
   - `01. Inbox/`, `02. Projects/`, `03. Areas/`, `04. Resources/`, `05. Archives/`

   If missing → STOP. Tell user: "Second Brain Setup isn't installed. Run ap-second-brain-setup first."

2. Confirm Digital Twin (Digital Twin) is installed. Check ALL of:
   - `02. Projects/Digital-Twin/` exists (the Digital Twin build pipeline)
   - `03. Areas/Self/digital-twin/` exists (the twin folder with 8 category subfolders)
   - At least one of:
     - `03. Areas/Self/atomic-notes/{tool}-{date}/` (chat-history-imported atomic notes)
     - `03. Areas/Self/atomic-notes/digital-twin-calibration-{date}/` (calibration interview notes)

   If Digital Twin isn't installed → STOP. Tell user: "Cartographer maps the atomic notes Digital Twin extracted. Run `setup-digital-twin.md` first (Digital Twin), then come back here."

   If Digital Twin IS installed but no chat-history atomic notes exist (user only did calibration, no chat export) → WARN: "Digital Twin ran but no chat-history was imported, so Cartographer has thin data to work with. It can still scan your calibration answers for domains. Continue?"

3. Check `_System/active-installs/work-atlas/` — if it exists, this is a RESUME. Read its `progress.md` and offer to continue from the last completed phase.

4. Cache existing Area folder names from `03. Areas/` so Phase 2 can offer "subfolder under existing Area" options. Also cache `02. Projects/` names for project-vs-area decisions.

5. Report:

   > "═══ CARTOGRAPHER — PRE-FLIGHT ═══
   >
   > Vault: ✓ installed
   > Digital Twin: ✓ installed (twin folder at 03. Areas/Self/digital-twin/)
   > Chat-history atomic notes detected: {count} notes across {N} folders
   > Calibration interview answers: {30 / N} questions answered
   > Existing Areas: {comma-separated list}
   > Active install (resume?): {none — fresh | DETECTED — last completed Phase {N}}
   >
   > Plan: scan all your atomic notes → detect work-domain clusters → walk through each with you to confirm → build folder structure → re-route notes → cross-reference back into your twin.
   >
   > Say 'go' to start (or 'resume' if active install detected)."

6. Wait for "go" or "resume."

═══════════════════════════════════════════════════════════
PHASE 1 — SCAN + DETECT WORK DOMAINS
═══════════════════════════════════════════════════════════

Print:
> "Phase 1 / 7 — Scanning your atomic notes for work-domain clusters..."

### Step 1.1 — Initialize install state

Create `_System/active-installs/work-atlas/`:
- `snapshot.md` — full copy of this Cartographer prompt (for resume)
- `progress.md` — phase status tracker (same pattern as Digital Twin)
- `domains-detected.md` — output of Phase 1 (the candidate domain list)
- `domains-confirmed.md` — output of Phase 2 (user's approved plan)

Also inject the Active Installs section into vault root `CLAUDE.md` if not already present (idempotent — same as Digital Twin Phase 1).

### Step 1.2 — Load source atomic notes

Read all atomic notes from these paths, filtered to `#source/user-statement`, `#source/user-belief`, AND `#source/digital-twin-calibration`:

- `03. Areas/Self/atomic-notes/**` (chat history + calibration outputs)
- `04. Resources/AtomicNotes/imported/**` (generic reference from chat)
- `01. Inbox/atomic-notes-from-*/**` (inbox-fallback notes from Digital Twin)

Ignore `#source/model-statement` — model output isn't user signal.

### Step 1.3 — Cluster by work domain

Cluster the notes into work-domain candidates. A work domain is a recurring topic where the user is DOING / LEARNING / DECIDING about something practical (not just reflecting on themselves).

Detection heuristics:
- **Frequency** — at least 10 notes mentioning the topic
- **Action verbs** — the user is doing things (writing, analysing, building, deciding, designing, calculating, structuring) — not just contemplating
- **Specificity** — the topic has concrete sub-elements (e.g., "copywriting" → headlines, hooks, CTAs)
- **Recurrence** — the topic appears across multiple conversation dates, not a one-off

Typical work domains to look for (examples — don't limit to these):
- Copywriting / Content Writing
- Marketing / Growth / Funnels
- Sales
- Investment / Finance / Trading
- Real Estate
- Code / Software Engineering
- Design / Visual Design
- Presentations / Slides / Decks
- Speaking / Presenting / Pitching
- Operations / Systems
- Product / UX
- Research / Analysis
- Negotiation
- Hiring / Leadership / Management
- Strategy / Planning
- Health / Fitness (if treated as practice, not just self-reflection)
- Parenting (if treated as a craft, not just identity)
- Music / Creative practice
- Teaching / Coaching / Training

For each detected cluster, capture:
- **Domain name** (short, kebab-case slug + display name)
- **Note count** — how many atomic notes belong to this domain
- **Source paths** — where the notes currently live
- **Sample notes** — 3–5 example note titles as evidence
- **Sub-themes** — recurring sub-topics within the domain (e.g., copywriting → hooks, headlines, email subject lines)
- **Existing Area match** — does this domain match an existing Area folder name (case-insensitive, fuzzy)? If yes, note which one.

Sort detected domains by note count (descending).

### Step 1.4 — Write the detected domains file

Write `_System/active-installs/work-atlas/domains-detected.md`:

```yaml
---
phase: 1
status: complete
total_domains_detected: {N}
total_notes_scanned: {M}
generated_at: {ISO timestamp}
---

# Detected Work Domains

{One section per detected domain}

## {Domain name}
- **Note count:** {N}
- **Source paths:** {list of folder paths where these notes live}
- **Sample notes:**
  - [[note-1-slug]]
  - [[note-2-slug]]
  - [[note-3-slug]]
- **Sub-themes:** {comma-separated list}
- **Existing Area match:** {none | 03. Areas/{name}}
```

### Step 1.5 — Report Phase 1

> "Phase 1 ✓ — Detected {N} work domains across {M} atomic notes:
> {numbered list: 1. {Domain} ({count} notes), 2. {Domain} ({count}), ...}
>
> Full detection report at `_System/active-installs/work-atlas/domains-detected.md`.
>
> Moving to Phase 2 — interactive review."

Update progress.md: `phase_1_scan: complete`, `phase_2_review: in-progress`.

═══════════════════════════════════════════════════════════
PHASE 2 — INTERACTIVE REVIEW
═══════════════════════════════════════════════════════════

Print:
> "Phase 2 / 7 — Walking through detected domains one at a time. For each, you tell me what to do. Type 'quit' anytime to save progress and resume later."

### Step 2.1 — Per-domain review loop

For each detected domain (in order, highest note count first), present:

```
─────────────────────────────────────────────
Domain {N} of {Total}: {Domain name}
─────────────────────────────────────────────

Detected based on {count} atomic notes across:
  - {path 1} ({X} notes)
  - {path 2} ({Y} notes)

Sample notes:
  - [[sample 1]]
  - [[sample 2]]
  - [[sample 3]]

Recurring sub-themes: {comma-separated list}

{If existing Area match found:}
NOTE: Your vault already has an area `03. Areas/{ExistingArea}/` that looks related.

What should I do with this domain?

  a) Create as new Area: `03. Areas/{Suggested Name}/`
  b) Add as subfolder under: `03. Areas/{ExistingArea}/{Suggested Subname}/`  (if existing match)
  c) Subfolder under a DIFFERENT existing area — tell me which one
  d) Rename — I'll suggest a different name for the folder
  e) Skip — don't create anything for this domain
  f) Quit — save progress and stop (resume by saying 'continue' later)
```

Capture user's choice. If `rename`, ask: "What should the folder be called?" Wait for answer.

If `subfolder under different`, list existing Areas and let user pick.

### Step 2.2 — Persist before progress

After EACH domain decision, write to `_System/active-installs/work-atlas/domains-confirmed.md`:

```yaml
---
phase: 2
status: in-progress
total_decisions: {N}
completed: {X}
---

# Confirmed Domain Decisions

| Domain | Decision | Destination |
|---|---|---|
| {name} | create-area | 03. Areas/{Name}/ |
| {name} | subfolder | 03. Areas/{Parent}/{Sub}/ |
| {name} | skip | — |
```

Update progress.md: increment `decisions_made`, update `last_updated`. Then move to the next domain.

If user types `quit`:
> "Decisions locked: {N} of {Total}. To resume, open Claude Code at your vault root and say 'continue' — I'll pick up at domain {N+1}."

### Step 2.3 — Phase 2 complete

When all domains reviewed:
> "Phase 2 ✓ — All {N} domain decisions captured. Summary:
> - Create as Area: {count}
> - Add as subfolder: {count}
> - Skipped: {count}
>
> Moving to Phase 3 — building the folder structure."

Update progress.md: `phase_2_review: complete`, `phase_3_create: in-progress`.

═══════════════════════════════════════════════════════════
PHASE 3 — CREATE FOLDER STRUCTURE
═══════════════════════════════════════════════════════════

Print:
> "Phase 3 / 7 — Creating folder structure..."

For each `create-area` decision, create:

```
03. Areas/{Domain Name}/
├── README.md
├── atomic-notes/
└── wiki/
```

For each `subfolder` decision, create:

```
03. Areas/{Parent}/{Sub}/
├── README.md
└── atomic-notes/
```

Each `README.md` template:

```markdown
---
tags: [type/area-readme, source/agent, source/work-atlas]
created: {TODAY}
created_by: Cartographer
source_atomic_notes: {note_count}
---

# {Domain / Subfolder Name}

> {1-sentence description: what kind of work / notes live in this area}

## Sub-themes (detected from atomic notes)

{bullet list of sub-themes from Phase 1}

## Sources

- Detected by Cartographer on {TODAY}
- Backed by {N} atomic notes imported from chat history
- Cross-referenced in [[digital-twin/6-domain-expertise/README]]
```

Skip any domain marked `skip` — don't create anything.

Update progress.md after each folder created. If a write fails, STOP and report.

Report:
> "Phase 3 ✓ — {N} folders created. Moving to Phase 4 — re-routing your notes."

Update progress.md: `phase_3_create: complete`, `phase_4_reroute: in-progress`.

═══════════════════════════════════════════════════════════
PHASE 4 — RE-ROUTE ATOMIC NOTES
═══════════════════════════════════════════════════════════

Print:
> "Phase 4 / 7 — Moving your atomic notes into their new homes..."

For each confirmed domain:
1. Find the atomic notes that belong to this domain (use the same clustering logic from Phase 1, refined by user's confirmations from Phase 2).
2. **Move (not copy)** those notes from their current location to the new destination:
   - If destination is a new Area: `03. Areas/{Domain}/atomic-notes/{original-source-tag}/{filename}`
   - If destination is a subfolder: `03. Areas/{Parent}/{Sub}/atomic-notes/{original-source-tag}/{filename}`
3. Preserve the `{speaker-tag}` subfolder structure (`user-statement/`, `user-belief/`, etc.)
4. After moving, search the vault for any `[[wikilinks]]` pointing to the old paths and update them to the new paths.

If two domains both claim a note (overlapping clusters), prefer the higher-frequency domain. Mention this to the user at the end as a "cross-domain note" report.

Persist progress.md after EACH batch of ~50 moves so resume can pick up mid-Phase-4.

Report:
> "Phase 4 ✓ — {N} notes re-routed across {M} new domains:
> {table: domain → notes moved}
>
> Cross-domain notes (assigned to highest-frequency domain): {count}
>
> Moving to Phase 5 — cross-referencing into your twin."

Update progress.md: `phase_4_reroute: complete`, `phase_5_crossref: in-progress`.

═══════════════════════════════════════════════════════════
PHASE 5 — CROSS-REFERENCE INTO DIGITAL TWIN
═══════════════════════════════════════════════════════════

Print:
> "Phase 5 / 7 — Cross-referencing the new domains back into your Digital Twin..."

### Step 5.1 — Update digital-twin/6-domain-expertise/README.md

Read the current `03. Areas/Self/digital-twin/6-domain-expertise/README.md`.

Append (or update existing) a "Mapped Areas" section:

```markdown
## Mapped Areas (from Cartographer)

These are the work domains Cartographer detected and mapped on {TODAY}:

- [[03. Areas/{Domain1}/README|{Domain1}]] — {note count} atomic notes, sub-themes: {top 3}
- [[03. Areas/{Domain2}/README|{Domain2}]] — {note count} atomic notes, sub-themes: {top 3}
- ...

Each linked Area is a navigable hub for that domain. The twin's Domain Expertise section above is the SUMMARY; these Areas are the DEPTH.
```

### Step 5.2 — Back-link each new Area's README to the twin

For each created Area's `README.md`, ensure the bottom has:

```markdown
## See also

- [[03. Areas/Self/digital-twin/6-domain-expertise/README|Domain Expertise (Digital Twin)]]
- [[03. Areas/Self/digital-twin/README|Master Digital Twin MOC]]
```

### Step 5.3 — Report

> "Phase 5 ✓ — Twin cross-references updated. Open `03. Areas/Self/digital-twin/6-domain-expertise/README.md` to see your new mapped Areas. The graph view in Obsidian (if installed) now shows the twin connected to your work domains.
>
> Moving to Phase 6 — registering the pack."

Update progress.md: `phase_5_crossref: complete`, `phase_6_register: in-progress`.

═══════════════════════════════════════════════════════════
PHASE 6 — REGISTER PACK
═══════════════════════════════════════════════════════════

Print:
> "Phase 6 / 7 — Registering Cartographer..."

Read `_System/INSTALLED-PACKS.md`. Append a row:

```
| work-atlas | Cartographer | {TODAY} | complete | {N} work domains mapped: {comma-separated names}. Folder structure created at 03. Areas/{...}. Atomic notes re-routed. Cross-referenced into digital-twin/6-domain-expertise/. |
```

Then clean up:
- Delete `_System/active-installs/work-atlas/` (install complete; resume state no longer needed)
- Keep `domains-detected.md` and `domains-confirmed.md` archived to `02. Projects/Digital-Twin/_archive/cartographer-{TODAY}/` for future reference

Update progress.md: `phase_6_register: complete`, `phase_7_closeout: in-progress`.

Report:
> "Phase 6 ✓ — Cartographer registered. Stack grew by {N} Areas."

═══════════════════════════════════════════════════════════
PHASE 7 — CLOSEOUT
═══════════════════════════════════════════════════════════

Print:

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║        CARTOGRAPHER INSTALLED ✓                  ║
║        THE CARTOGRAPHER                          ║
║                                                  ║
╚══════════════════════════════════════════════════╝

What you unlocked:
  ✓ {N} work domains detected and confirmed
  ✓ {X} new Areas created at 03. Areas/
  ✓ {Y} subfolders added under existing Areas
  ✓ {Z} atomic notes re-routed into their proper home
  ✓ Cross-references in 03. Areas/Self/digital-twin/6-domain-expertise/

What to do next:
  - Browse your new Areas. Each has its own atomic-notes/ folder waiting to grow.
  - Test the depth: ask Claude Code "draft me a {domain} piece in my voice, grounded against 03. Areas/{Domain}/" — it'll ground against the domain notes specifically.
  - If Obsidian is installed, open graph view — the twin should now branch into your work Areas as connected clusters.

Future packs that build on this foundation:
  Triage Inbox (ap-triage-inbox): daily routing of new captures (now smarter because it knows your domains)
```

Update progress.md: all phases complete. Update `02. Projects/Digital-Twin/progress.md` to reflect Cartographer pass completed.

═══════════════════════════════════════════════════════════
SAFEGUARDS
═══════════════════════════════════════════════════════════

- **Pre-flight non-negotiable.** Don't proceed past Phase 0 if Second Brain Setup + Digital Twin aren't both installed.
- **Persist before progress** in EVERY phase. Each domain decision in Phase 2 commits before the next. Each folder created in Phase 3 commits. Each re-route batch in Phase 4 commits.
- **Compaction-resistant.** State lives in `_System/active-installs/work-atlas/` + `02. Projects/Digital-Twin/_archive/cartographer-{date}/`. Resume = open new session, say "continue."
- **Idempotent.** Re-running detects existing state and offers to resume rather than overwriting.
- **MOVE, don't COPY** in Phase 4 — atomic notes belong in ONE place. Update wikilinks after moves.
- **Don't fabricate domains.** Phase 1 detection only surfaces clusters with ≥10 notes. If a user has thin chat history, surface fewer domains, not made-up ones.
- **User decides per domain.** Phase 2 is interactive — no autonomous folder creation. If user types 'skip' for a domain, that domain's notes stay where they are.

═══════════════════════════════════════════════════════════

End of prompt. Run Phase 0 now: check pre-flight, report, wait for "go."
