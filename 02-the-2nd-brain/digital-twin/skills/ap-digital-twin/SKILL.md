---
name: ap-digital-twin
description: "Run the full Digital Twin pipeline in a Second Brain Setup vault: detect a chat export, extract atomic notes in waves, run a 30-question calibration interview, synthesise a digital-twin folder, map work domains and draft wiki articles, resumable at every phase. Use for \"make my digital twin\" or \"continue\" during an install."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Digital Twin

You are installing DIGITAL TWIN.

This is a consolidated expansion pack that runs the full Digital Twin pipeline end-to-end — capturing WHO you are (Phases 1–4) then mapping WHAT YOU DO via Cartographer step (Phase 5):

  Phase 0  Pre-flight + auto-detect chat export
  Phase 1  Install Project Digital Twin + enable resume capability
  Phase 2  Memory Import (parallel waves) — if chat export present
  Phase 3  Calibration Interview (30 questions, resumable per-question)
  Phase 4  Twin Synthesis — map-reduce into a digital-twin/ folder (not one file)
  Phase 5  Cartographer — detect work domains and map them into Areas
  Phase 6  Multi-Topic Wiki Drafts — many articles, one per major theme
  Phase 7  Register pack as COMPLETE + clean up install state
  Phase 8  Closeout

CRITICAL DESIGN: every phase persists progress to disk BEFORE moving on. Inside Phase 2, each parallel wave commits before the next. Inside Phase 3, each Q+A locks before the next question. Inside Phase 5, each domain decision and each batch of note moves commits before the next. The user can quit at ANY point, open a new Claude Code session, type "continue," and you (or a future Claude session reading CLAUDE.md) will resume exactly where they left off — no re-paste required.

Read this whole prompt before doing anything. Don't run anything until I say "go."

═══════════════════════════════════════════════════════════
PHASE 0 — PRE-FLIGHT + AUTO-DETECT
═══════════════════════════════════════════════════════════

1. Confirm vault root. Verify the following exist (relative to current directory):
   - `CLAUDE.md` (root operating manual)
   - `_System/` (with TAG_TAXONOMY.md, VAULT_MANIFEST.md, LINKING_RULES.md)
   - `01. Inbox/`
   - `02. Projects/`
   - `03. Areas/`
   - `04. Resources/`
   - `05. Archives/`

   If any are missing, STOP. Tell the user: "Second Brain Setup isn't installed yet. Run ap-second-brain-setup first."

2. Read `_System/VAULT_MANIFEST.md`. Note which routines are installed: Triage Inbox (ap-triage-inbox), Weekly Sweep (ap-weekly-sweep) and Import AI Exports (ap-import-ai-exports).

3. **Auto-detect chat export.** Don't require the user to have named the folder. Search `01. Inbox/` recursively for any folder containing a `conversations.json` file. Also detect:
   - Claude exports (also contain `conversations.json`)
   - Gemini Takeout (look for HTML files under `My Activity/`-style folders)
   - Perplexity / other (look for any JSON/markdown that has clear user/assistant role markers)

   For each found export:
   - Identify the source tool (chatgpt | claude | gemini | perplexity | other) by inspecting the JSON structure (ChatGPT has `mapping` fields with `author.role`; Claude has different schema)
   - Get the date — either from a filename, from frontmatter inside the export, or fall back to today's date
   - Note the original folder name

4. **Filter to actual chat history. KEEP for extraction:**
   - `conversations.json` — THE primary source of truth
   - `shared_conversations.json` — merge with conversations.json if present
   - Gemini Takeout per-conversation `.html` files (only if no JSON equivalent)
   - Other JSON/markdown only if you open them and verify they contain user/assistant role markers and message text

   **IGNORE entirely:**
   - `chat.html` — duplicate of conversations.json in human-readable form, no need
   - `dalle-generations/`, `audio/`, `voice/`, `recordings/` folders
   - `user.json`, `message_feedback.json`, `model_comparisons.json`
   - All image files (`*.png`, `*.jpg`, `*.jpeg`, `*.gif`, `*.webp`, `*.svg`)
   - All media files (`*.mp4`, `*.mp3`, `*.wav`, `*.webm`, `*.m4a`, `*.ogg`)
   - PDFs, binaries, navigational `README` / `index.html`
   - Hidden files (`.DS_Store`, etc.)

5. Count the conversations in the kept file(s).

6. Read existing folder names under `02. Projects/` and `03. Areas/` — cache them for Phase 2 topic routing and Phase 5 Cartographer review.

7. Check `03. Areas/Self/digital-twin/` — does it exist? Determines whether Phase 4 is fresh-create or merge.

8. Check `_System/active-installs/digital-twin/` — if it exists, this is a RESUME case. Read its `progress.md` and offer to continue from the last completed phase. If it doesn't exist, this is a fresh install.

9. Check if `.obsidian/` exists at the vault root — that's Obsidian's config directory and indicates the vault has already been opened in Obsidian at least once. Cache the result for Phase 4 and Phase 8 to reference. (Not a blocker — Digital Twin works without it; the graph payoff just won't visualize until Obsidian is set up.)

10. Report and confirm:

    > "═══ DIGITAL TWIN — PRE-FLIGHT ═══
    >
    > Vault: ✓ installed
    > Chat export found: {one of the following options}
    >   ▸ "Yes — detected ChatGPT export at `01. Inbox/{original-folder-name}/`. {N} conversations in conversations.json. (Ignored {X} media/metadata files.) I'll rename the folder to `chat-export-chatgpt-{YYYY-MM-DD}/` for tidiness if you confirm."
    >   ▸ "No export detected. Phase 2 will be skipped — straight to the interview. Phase 5 (Cartographer) will still run on whatever calibration-derived notes Phase 3 produces, but with thinner data."
    > Existing twin folder (03. Areas/Self/digital-twin/): {none — will create fresh | exists — Phase 4 will merge per-category}
    > Active install: {none — fresh install | DETECTED — last completed phase was Phase {N} at {timestamp}. Resume?}
    > Obsidian: {detected at .obsidian/ — graph view will work once Digital Twin finishes | NOT detected — install obsidian.md and 'Open folder as vault' on this folder to see the graph after Digital Twin. Not required to proceed.}
    >
    > Plan: {summary of which phases will run, based on detected state — note the 8-phase flow, with Phase 5 Cartographer mapping your work domains after the SELF twin is synthesized}
    >
    > Say 'go' to start (or 'resume' if active install detected)."

11. Wait for "go" or "resume."

12. If the user confirms, rename the detected export folder from its original name to `01. Inbox/chat-export-{tool}-{YYYY-MM-DD}/`. Do this via `mv`. Confirm: "Renamed to `chat-export-{tool}-{date}/`."

═══════════════════════════════════════════════════════════
PHASE 1 — INSTALL PROJECT DIGITAL TWIN + ENABLE RESUME
═══════════════════════════════════════════════════════════

Print:
> "Phase 1 / 8 — Installing Project Digital Twin and enabling resume-from-anywhere..."

### Step 1.1 — Create the Active Install state

Create `_System/active-installs/digital-twin/` with:

- `snapshot.md` — copy the FULL contents of this Digital Twin prompt verbatim (the entire ```` ```` block you're reading right now). This is what a future session reads to know what install they're in the middle of.
- `progress.md` — single source of truth for resume. Template:

```yaml
---
pack: "01 — Digital Twin"
installer: setup-digital-twin.md
status: in-progress
started: {YYYY-MM-DD HH:MM}
last_updated: {YYYY-MM-DD HH:MM}
phases:
  phase_0_preflight: complete
  phase_1_install: in-progress
  phase_2_memory_import: pending
  phase_3_calibration: pending
  phase_4_synthesis: pending
  phase_5_cartographer: pending
  phase_6_wiki_drafts: pending
  phase_7_register: pending
  phase_8_closeout: pending
phase_2:
  total_conversations: {N or null}
  chunks_total: {N or null}
  chunks_complete: 0
  notes_extracted: 0
phase_3:
  total_questions: 30
  completed: 0
  skipped: 0
  last_completed_question: null
phase_4:
  categories_total: 8
  categories_complete: 0
phase_5:
  scan_complete: false
  domains_detected: null
  domains_total: null
  decisions_made: 0
  folders_created: 0
  notes_rerouted: 0
phase_6:
  topics_total: null
  drafts_complete: 0
---

# Digital Twin Install Progress

## Resume instructions for future sessions

Read `_System/active-installs/digital-twin/snapshot.md` — that's the full pack prompt. Find the first phase marked `pending` or `in-progress` in this frontmatter. Resume from there.

## Phase-by-phase status

(Updated by the installer after each phase completes.)
```

### Step 1.2 — Inject Active Installs section into vault root CLAUDE.md

Read the vault root `CLAUDE.md`. Search for the heading `## Active Installs`. If it doesn't exist, append this section to the end of the file:

```markdown
---

## Active Installs

If the user says "continue", "resume install", "where did I leave off", or similar — check `_System/active-installs/`. Each subdirectory there represents an in-progress expansion pack install.

For each active install:
1. Read its `progress.md` to find the last completed phase/step
2. Read its `snapshot.md` for the full original install prompt
3. Resume execution from the first phase marked `pending` or `in-progress` in `progress.md`

No re-paste required. The install state is fully on disk.

When an install completes, the pack deletes its `_System/active-installs/{pack-id}/` directory.
```

If the section already exists, leave it alone (idempotent).

### Step 1.3 — Create the Project Digital Twin folder

Create `02. Projects/Digital-Twin/` with:

```
02. Projects/Digital-Twin/
├── CLAUDE.md          (project operating manual)
├── README.md          (project overview)
├── progress.md        (mirrors _System/active-installs/digital-twin/progress.md during install)
├── questions/         (one .md per calibration question — populated in Phase 3)
└── _drafts/           (category synthesis drafts — populated in Phase 4)
```

Templates:

**`02. Projects/Digital-Twin/CLAUDE.md`:**

```markdown
# Project Digital Twin — Operating Manual

> Read the vault-root CLAUDE.md first (vault-wide rules), then this file (project-specific rules).

## What this project is

Your Digital Twin is the second brain's understanding of YOU. This project is the BUILD pipeline — where the twin gets calibrated and re-calibrated.

The twin itself lives at `03. Areas/Self/digital-twin/` (NOT in this project folder). It's a FOLDER of category subfolders, not a single file — there's more in there than fits on one page.

## How to operate inside this project

- `progress.md` — the resume single-source-of-truth (mirrors `_System/active-installs/digital-twin/progress.md` during install)
- `questions/` — one .md per interview question with locked status and source citations
- `_drafts/` — running category synthesis drafts (cleaned up after Phase 4)
- `_archive/cartographer-{date}/` — domains-detected.md + domains-confirmed.md from each Cartographer pass (Phase 5)
- When a calibration pass completes, archive `questions/` to `_archive/{date}/` — the twin folder in Self persists ongoing

## Hard rules

- Persist before progress: never advance a step without writing the current state to disk
- The twin lives at `03. Areas/Self/digital-twin/` — this project is build pipeline only
- Never confuse model output with user voice: only `#source/user-statement`, `#source/user-belief`, `#source/digital-twin-calibration` count as the user's words

## Status

See `progress.md`.
```

**`02. Projects/Digital-Twin/README.md`:**

```markdown
# Project Digital Twin

The build pipeline for calibrating the second brain's understanding of who I am and what I do.

- **Started:** {TODAY}
- **Stage:** active

## Build pipeline

1. **Memory Import** — extract years of LLM chat into atomic notes (breadth)
2. **Calibration Interview** — 30 deep questions with vault-sourced candidate answers (depth)
3. **Twin Synthesis** — map-reduce into `03. Areas/Self/digital-twin/` (8 category folders + master index)
4. **Cartographer** — detect work domains in the atomic notes, build Areas folder structure, re-route notes, cross-reference back into the twin
5. **Multi-Topic Wiki Drafts** — distill major themes into `_System/wiki/drafts/`

## Re-runs

Re-running the Calibration Interview every 6–12 months keeps the twin current. Archive prior `questions/` to `_archive/{date}/` before a fresh pass. Re-running Cartographer makes sense after major life/work shifts — archive `_archive/cartographer-{date}/` from the prior pass before re-running.
```

### Step 1.4 — Create the empty twin folder scaffolding

Create `03. Areas/Self/digital-twin/` with empty category subdirectories (Phase 4 fills them):

```
03. Areas/Self/digital-twin/
├── README.md           (stub — Phase 4 reduce agent overwrites)
├── 1-voice/
├── 2-values/
├── 3-mental-models/
├── 4-goals/
├── 5-decision-criteria/
├── 6-domain-expertise/
├── 7-heroes-influences/
└── 8-open-questions/
```

Write a stub README.md in the root and in each subdirectory ("Awaiting synthesis from Phase 4 of Digital Twin install.").

### Step 1.5 — Persist progress

Update `_System/active-installs/digital-twin/progress.md`: `phase_1_install: complete`, `phase_2_memory_import: in-progress` (if export found, else `skipped — no export`). Mirror to `02. Projects/Digital-Twin/progress.md`. Update `last_updated`.

Print:
> "Phase 1 ✓ — Project Digital Twin installed at `02. Projects/Digital-Twin/`. Resume capability enabled (you can quit anytime and pick up by saying 'continue' in a new session). Twin folder scaffolded at `03. Areas/Self/digital-twin/` — ready to fill. Moving to Phase 2..."

═══════════════════════════════════════════════════════════
PHASE 2 — MEMORY IMPORT (parallel waves)
═══════════════════════════════════════════════════════════

If NO chat export was found, skip. Update progress.md: `phase_2_memory_import: skipped — no export`. Move to Phase 3.

Otherwise:

Print:
> "Phase 2 / 8 — Memory Import.
>
> Heads up: this is the first taste of what the **Triage Inbox** skill (ap-triage-inbox) automates. Today I'm doing it manually at scale — taking everything in your export and classifying every turn. A future pack will turn this same logic into a daily habit for new captures.
>
> Spawning parallel sub-agents. Aiming for maximum throughput — extracting from your {N} conversations should take ~5–15 minutes depending on size."

### Step 2.1 — Plan parallel chunks

- Total conversations: N (from Phase 0)
- Target: ~10 parallel sub-agents per wave (Claude Code tool limit)
- Chunk size: `ceil(N / 10)` conversations per agent (so one wave handles all of them) — but cap at 30 per chunk to keep each agent's context manageable. If N > 300, run multiple waves.
- Example: 250 conversations → 1 wave of 10 agents × 25 chunks each
- Example: 800 conversations → 2 waves of ~10 agents × 40 each (capped, so really 3 waves × 30 each)

Write the chunk plan to `02. Projects/Digital-Twin/_drafts/phase-2-chunk-plan.md` with: chunk ID, conversation indices, status (pending / in-progress / complete), output path.

Update progress.md: `phase_2.chunks_total: {N}`.

### Step 2.2 — Sub-agent instruction set (every extraction agent uses this)

This block is the complete prompt every chunk agent gets in Step 2.3. Self-contained — no external files needed.

**THE GOLDEN RULE — speaker taxonomy:**

A chat is a conversation. Each turn has a speaker:
- **USER** — the person who owns this vault (NOT the model)
- **MODEL** — the AI they were talking to (NOT them)

A model statement is NOT the user's belief. Common failure mode: the model wrote "you should approach this with stoic detachment" — that's the MODEL's recommendation, NOT the user's view. Don't turn that into "user values stoic detachment." Even when the user asked the model to "write in my voice," the model's output is still the MODEL'S words.

Treatment matrix:

| Source | Captured as | Counts as user belief? |
|---|---|---|
| What the user said in a chat | atomic note tagged `#source/user-statement` | YES (high confidence) |
| User said + clearly endorsed model output ("yes exactly") | atomic note tagged `#source/user-belief` | YES (high confidence) |
| User said + pushed back ("no, I disagree…") | atomic note of the pushback, tagged `#source/user-belief` | YES (the pushback IS the user's view) |
| Model output the user didn't react to | atomic note tagged `#source/model-statement` | NO (information they were exposed to, not a belief) |
| Model output the user explicitly disagreed with | atomic note tagged `#source/model-rejected` | NO (and useful negative signal) |

Phase 4 synthesis reads ONLY `#source/user-statement`, `#source/user-belief`, and `#source/model-rejected` (as negative signal). It IGNORES `#source/model-statement`.

**ATOMIC NOTE TEMPLATE:**

```yaml
---
tags: [type/atomic, source/chat-export, source/{speaker-tag}]
captured: {YYYY-MM-DD when extracted}
conversation_date: {date of the chat if available}
conversation_title: {truncated to 80 chars}
tool: chatgpt | claude | gemini | perplexity | other
speaker: user | model | user-belief | model-rejected
confidence: high | medium | low
---

# {one-sentence fact}

{optional: 1–2 lines of context if the fact is hard to understand standalone}
```

**SPEAKER TAG VALUES:**
- `user-statement` — direct user words
- `user-belief` — confirmed user belief (direct or via clear endorsement of model output)
- `model-statement` — model said this, user didn't react
- `model-rejected` — model said this, user pushed back

**FILENAME:** `{speaker}-{kebab-slug-of-the-fact}.md` (max 80 chars). Examples:
- `user-belief-prefers-bullet-points-over-prose.md`
- `model-statement-stoicism-roots-back-to-zeno-of-citium.md`
- `model-rejected-suffering-comes-only-from-attachment.md`

**WHAT COUNTS AS AN ATOMIC NOTE:**
- ONE self-contained fact, opinion, decision, preference, frustration, question, or insight per note
- Stated as a single sentence in the note body
- Has the frontmatter above

**WHAT DOES NOT COUNT (skip):**
- Filler / pleasantries ("thanks", "ok", "got it")
- Pure procedural exchanges ("can you reformat this")
- Direct verbatim copies of model output (summarise the FACT instead — don't quote the prose)

**TOPIC ROUTING — every note saves to the folder matching its topic:**

1. **About-the-user** — values, voice, identity, frameworks, mental models, decisions, goals, frustrations, communication style:
   → `03. Areas/Self/atomic-notes/{tool}-{export-date}/{speaker-tag}/`

2. **About a known project** — note clearly references a project that matches a subfolder under `02. Projects/` (case-insensitive fuzzy match):
   → `02. Projects/{ProjectName}/atomic-notes/{tool}-{export-date}/{speaker-tag}/`

3. **About a known area / pillar** — matches a subfolder under `03. Areas/` (Health, Family, Faith, work pillars, etc.):
   → `03. Areas/{AreaName}/atomic-notes/{tool}-{export-date}/{speaker-tag}/`

4. **Generic reference** — a fact/definition/framework NOT about the user personally and NOT tied to a project/area (e.g. "Stoicism originated with Zeno of Citium"):
   → `04. Resources/AtomicNotes/imported/{tool}-{export-date}/{speaker-tag}/`

5. **Unclear / spans multiple** — can't confidently route:
   → `01. Inbox/atomic-notes-from-{tool}-{export-date}/{speaker-tag}/`

When in doubt, prefer Inbox over Resources. Inbox gets triaged; Resources is a destination. For `#source/model-statement` notes, default to `04. Resources/AtomicNotes/` unless clearly user-specific.

**PII FLAGGING:** If a conversation contains passwords, full credit card numbers, SSNs, full home addresses, or sensitive medical details — FLAG the conversation file path in the report-back and DO NOT extract those notes. Surface the full list to the user at the end of Phase 2.

### Step 2.3 — Run each wave (spawn the agents)

For each wave: spawn ALL the chunk agents in a SINGLE message with multiple Agent tool calls (parallel execution). Each agent receives:

- Its conversation slice (specific indices in conversations.json)
- **The complete Step 2.2 instruction set above, pasted verbatim into the agent's prompt** (this is what makes the agents self-contained)
- The cached project/area names from Phase 0 step 6 (for fuzzy-matching topic routing)
- Report-back format: count of notes written per speaker tag + per destination folder + any PII flags

After each wave completes:
- Update `_System/active-installs/digital-twin/progress.md`: increment `chunks_complete`, update `notes_extracted` total, update `last_updated`
- Mirror to `02. Projects/Digital-Twin/progress.md`

This way if the user quits mid-Phase-2, resume picks up at the next pending chunk.

### Step 2.3 — Report Phase 2 complete

> "Phase 2 ✓ — Memory Import complete.
> Total atomic notes: {total}
>   user-statement: {U}
>   user-belief: {B}
>   model-statement: {M} (kept for context, not used for the twin)
>   model-rejected: {R} (used as negative signal in synthesis)
> Routed to: Self ({S}), Projects ({P}), Areas ({A}), Resources ({R}), Inbox-fallback ({I})
> PII flagged: {count} conversations — surfaced separately for your review
>
> Moving to Phase 3..."

Update progress.md: `phase_2_memory_import: complete`, `phase_3_calibration: in-progress`.

═══════════════════════════════════════════════════════════
PHASE 3 — CALIBRATION INTERVIEW
═══════════════════════════════════════════════════════════

Print:
> "Phase 3 / 8 — Calibration Interview.
>
> 30 questions across 8 sections. ~60 minutes if you do it in one sitting — but you don't have to. After every question I lock your answer to disk and update progress. Quit anytime by typing 'quit'. To pick up later, just open Claude Code in your vault and say 'continue' — I'll find where you left off.
>
> For each question, I'll FIRST check your atomic notes (including everything I just extracted in Phase 2) and offer a candidate answer. You confirm, clarify, update, or skip — much faster than answering cold.
>
> Ready? Say 'start' to begin question A1."

### Step 3.1 — Per-question loop

For each of the 30 questions in order (full list in Step 3.2 below), execute these steps:

**Step A — Search vault for prior context**

Search these locations for content relevant to the current question:
- `03. Areas/Self/atomic-notes/` (all subfolders)
- `04. Resources/AtomicNotes/` (all subfolders)
- `02. Projects/Digital-Twin/_archive/*/questions/*.md` (any prior calibration passes)
- Any existing `03. Areas/Self/digital-twin/{N-category}/` folder (prior twin synthesis)

Filter to notes tagged `#source/user-statement`, `#source/user-belief`, or `#source/digital-twin-calibration` only. Ignore `#source/model-statement` — not the user's voice.

Score by relevance (keyword + topic match against the question's section + the question text itself).

**Step B — Synthesize a candidate answer**

If 1+ relevant notes/profile snippets are found, synthesize a SHORT candidate answer (2–5 sentences). Cite the strongest source notes inline as wikilinks so the user can see where it came from.

If nothing relevant is found, candidate = `none`.

**Step C — Present the question**

When a candidate exists, format like this:

```
─────────────────────────────────────────────
Section {X} — {Section Title}     ({Done}/30 done)
Question {X}{N}: {question text}
─────────────────────────────────────────────

Based on what you've said in your prior notes, here's what I think:

> {candidate answer, 2–5 sentences}
> (sourced from: [[note-name-1]], [[note-name-2]], ...)

Options:
  confirm  — lock this in as my answer
  clarify  — keep the gist, but I want to add detail
  update   — replace with a fresh answer (this is stale or wrong)
  skip     — pass for now (mark skipped, you can come back)
  quit     — save progress and stop (resume by saying 'continue' in a new session)
```

When no candidate exists:

```
─────────────────────────────────────────────
Section {X} — {Section Title}     ({Done}/30 done)
Question {X}{N}: {question text}
─────────────────────────────────────────────

No prior context for this in your vault. Take a moment.

Options:
  answer  — type your answer
  skip    — pass for now
  quit    — save progress and stop
```

**Step D — Capture the user's response**

- **confirm** → final answer = candidate. Status: `locked`.
- **clarify** → ask "What would you add or refine?" Wait. Final answer = candidate + elaboration. Status: `clarified`.
- **update** → ask "What's the fresh answer?" Wait. Final answer = user's new answer. Status: `updated`.
- **answer** → wait for the answer. Final answer = what the user typed. Status: `locked`.
- **skip** → final answer = `(skipped)`. Status: `skipped`.
- **quit** → save state, stop. Don't ask the next question.

**3-level escalation on vague answers.** For `clarify`, `update`, and `answer`: if the response is surface-level (clichés, abstractions, "I value freedom"), escalate:
- L1: "Can you give me a specific example?"
- L2: "Walk me through what actually happened — what did you do, what did you say?"
- L3: "What did that cost you? What did you lose, gain, or feel?"

After three escalations, accept whatever the user gives and move on.

**Step E — PERSIST BEFORE MOVING ON (non-negotiable)**

Before asking the next question, write all of this to disk:

1. **Question file** at `02. Projects/Digital-Twin/questions/{section}-{Q-id}-{kebab-slug}.md`:

   ```yaml
   ---
   question_id: {X}{N}
   section: {section letter and title}
   status: locked | clarified | updated | skipped
   asked_at: {ISO timestamp}
   locked_at: {ISO timestamp}
   candidate_source: {comma-separated source note names, or "none"}
   ---

   # Q {X}{N}
   {question text}

   ## Candidate (from vault)
   {candidate answer, or "none"}

   ## Final answer
   {user's final answer}

   ## Atomic notes extracted
   - [[note-1-slug]]
   - [[note-2-slug]]
   ```

2. **Atomic notes** extracted from the final answer (one self-contained fact per note), tagged `#type/atomic`, `#source/digital-twin-calibration`, `#source/user-belief`. Topic-routed via the same 5-rule routing from Phase 2 Step 2.2. Most calibration answers route to `03. Areas/Self/atomic-notes/digital-twin-calibration-{YYYY-MM-DD}/`.

3. **progress.md updates** at BOTH `_System/active-installs/digital-twin/progress.md` AND `02. Projects/Digital-Twin/progress.md`: increment `completed` (or `skipped`), set `last_completed_question`, update `last_updated`.

If any write fails, STOP and report. Don't proceed on partial state.

**Step F — Move to next question**

Loop back to Step A with the next question in order.

If the user types `quit` during any question:
> "Question {N} locked. Progress saved. To resume, open Claude Code at your vault root in a new session and say 'continue' — I'll pick up at question {next}."

If the user types `synthesize now` (early synthesis with partial answers):
> "You've answered {N} of 30. I can synthesize the twin now with partial data, or you can finish first. Which?"

### Step 3.2 — The 30 Questions

**Section A — Identity & Origin (5 questions)**

- **A1.** What's your origin story — the chain of events that shaped who you are today? Three or four key chapters.
- **A2.** What were you like as a kid? What lit you up before anyone told you what you should be?
- **A3.** What's the hardest thing you've been through, and what did it teach you about yourself?
- **A4.** Forget your job title. In three sentences, who are you?
- **A5.** What do you want to be true about yourself in 10 years that isn't true today?

**Section B — Vision & Goals (5 questions)**

- **B1.** Describe your ideal Tuesday in 10 years. Who's there. What you're doing. How it feels.
- **B2.** What's the one thing you want to build, create, or accomplish in your lifetime — even if no one ever knew you did it?
- **B3.** What problem are you uniquely positioned to solve? Why you?
- **B4.** If money was unlimited and status was off the table, what would you spend your time doing?
- **B5.** What's the gap between where you are now and where you said in B1 — what's actually missing?

**Section C — Values & Priorities (4 questions)**

- **C1.** What are 3–5 things you refuse to compromise on, even when it costs you?
- **C2.** What makes you angry? Real anger, not performative outrage. (Anger reveals values.)
- **C3.** Tell me about a recent decision where you chose the harder path because of a principle. What was the principle?
- **C4.** What's the worst thing someone could honestly say about you that would actually sting?

**Section D — Skills & Assets (4 questions)**

- **D1.** What do you do that comes easy to you but seems hard to most people?
- **D2.** What do you do for free that others charge for?
- **D3.** What's your unique combination of skills, experiences, or perspectives — the intersection that nobody else has?
- **D4.** Where do you have unfair advantages — relationships, knowledge, access, a head start?

**Section E — Mental Models & How You Think (4 questions)**

- **E1.** When you have a hard decision, what frameworks or questions do you reach for?
- **E2.** What's a belief you hold that most smart people would disagree with — and you'd defend?
- **E3.** What's a question you've been wrestling with for years and still don't have a clean answer to?
- **E4.** How do you know when something is "true"? What's your bullshit-detector?

**Section F — Heroes & Influences (3 questions)**

- **F1.** Who are 5–10 people — alive or dead, known or unknown — who've shaped how you think? For each, what specifically did they teach you?
- **F2.** What books, essays, talks, or ideas keep coming back to you? Not the trendy ones — the ones that actually rewired you.
- **F3.** Who do you study? And who do you NOT study that you probably should?

**Section G — Pain Points & Frustrations (3 questions)**

- **G1.** What's the recurring frustration in your work or life — the thing that comes back every few months?
- **G2.** What are you avoiding right now? Something you know you should face but haven't.
- **G3.** What's the thing you should stop doing but haven't been able to?

**Section H — Energy & Success (2 questions)**

- **H1.** When are you most alive? What conditions produce your best work?
- **H2.** What does "successful next 12 months" look like, concretely? Three specific outcomes — not vibes.

### Step 3.2 — Phase 3 complete

When all 30 answered (or user explicitly says "synthesize now"):
> "Phase 3 ✓ — Calibration complete. {N} questions answered, {S} skipped. Moving to Phase 4..."

Update progress.md: `phase_3_calibration: complete`, `phase_4_synthesis: in-progress`.

═══════════════════════════════════════════════════════════
PHASE 4 — TWIN SYNTHESIS (single agent, vault-shaped output)
═══════════════════════════════════════════════════════════

Print:
> "Phase 4 / 8 — Twin Synthesis.
>
> One agent reads every belief-relevant atomic note + your 30 calibration answers in a single 1M-context pass, clusters them into 8 categories, and writes a vault-shaped twin folder with heavy wikilinks and MOCs (Maps of Content) at every level. That's what'll make your graph view light up in Obsidian.
>
> Why one agent, not eight: synthesis means spotting CROSS-category patterns ('freedom shows up in Values + Goals + Decision Criteria — it's a meta-driver'). Parallel agents can't see each other's work — they'd miss the connections that make the twin feel like a person, not eight disconnected slices. The atomic notes are small enough (typically ~1–3MB filtered) that one agent with 1M context handles them comfortably.
>
> Spawning the synthesiser now..."

### Step 4.1 — Spawn the single synthesiser

Spawn ONE sub-agent. Use a model with 1M context (e.g., Claude Opus or Sonnet 4.6 with 1M context window). The agent's full instructions:

1. **Load all belief-relevant atomic notes.** Search these paths:
   - `03. Areas/Self/atomic-notes/`
   - `02. Projects/*/atomic-notes/`
   - `03. Areas/*/atomic-notes/`
   - `04. Resources/AtomicNotes/imported/`

   Filter to notes tagged any of: `#source/user-statement`, `#source/user-belief`, `#source/digital-twin-calibration`, OR `#source/model-rejected` (use this as negative signal — "what I'm not"). IGNORE `#source/model-statement` for belief inference.

2. **Load all 30 calibration question files** from `02. Projects/Digital-Twin/questions/` — these are the deepest user-voice signal in the vault.

3. **Cluster** the patterns into 8 categories. For each category, identify 3–8 distinct sub-themes. Cross-category awareness is the whole point — actively note when a pattern appears in multiple categories (those become the master MOC's cross-cutting themes).

4. **Write the twin folder** at `03. Areas/Self/digital-twin/` in this order (write categories first, master MOC LAST — if interrupted, partial completion is recoverable):

   **Sub-theme files first** — one file per sub-theme inside each `{N-category}/` folder:
   ```yaml
   ---
   tags: [type/digital-twin, source/digital-twin-synthesis, category/{slug}, theme/{theme-slug}]
   twin_version: {N}
   ---

   # {Sub-theme name}

   {1-paragraph definition: what this pattern is, in the user's own framing}

   ## Where it shows up
   - {behavior or context 1} — see [[atomic-notes/source-note-1]]
   - {behavior or context 2} — see [[atomic-notes/source-note-2]]
   - {behavior or context 3} — see [[atomic-notes/source-note-3]]

   ## Signature phrases / behaviors
   - "{exact phrase or behavior 1}"
   - "{exact phrase or behavior 2}"

   ## See also
   - [[{related sub-theme in same category}]]
   - [[{N-category}/README]] — back to the category MOC
   - [[{related sub-theme in DIFFERENT category}]] — cross-link where the pattern bridges categories
   ```

   **Category MOCs second** — `{N-category}/README.md` for each of the 8 categories:
   ```yaml
   ---
   tags: [type/digital-twin, type/moc, source/digital-twin-synthesis, category/{slug}]
   twin_version: {N}
   ---

   # {Category name}

   > {1-paragraph category summary in the user's framing}

   ## Sub-themes in this category
   - [[1-voice/signature-phrases]] — {one-line teaser}
   - [[1-voice/em-dash-and-emphasis]] — {one-line teaser}
   - {etc.}

   ## Cross-references
   {This is where the magic happens. List sub-themes from OTHER categories that connect to themes here.}
   - [[3-mental-models/first-principles-thinking]] — feeds the "precision" thread in voice
   - [[5-decision-criteria/life-razor]] — shapes the tone of how decisions get communicated
   - {etc.}

   ## Back to top
   - [[digital-twin/README|Master Digital Twin MOC]]
   ```

   **Master MOC LAST** — `03. Areas/Self/digital-twin/README.md`:
   ```yaml
   ---
   tags: [type/digital-twin, type/moc, source/digital-twin-synthesis]
   twin_version: {N}
   last_calibrated: {TODAY}
   sources:
     - "{N} atomic notes from chat history extraction"
     - "30 calibration interview answers"
   ---

   # Digital Twin — Master Map

   > {1-paragraph identity statement — who this person is, in one tight paragraph the AI can ground against}

   ## Cross-cutting themes
   {The big patterns that span multiple categories. 3–5 of these.}

   ### {Theme 1 name}
   {1-paragraph description.} Appears in: [[1-voice/README|Voice]], [[3-mental-models/README|Mental Models]], [[5-decision-criteria/README|Decision Criteria]].

   ### {Theme 2 name}
   ...

   ## Category index
   - [[1-voice/README|Voice & Communication Style]] — {one-line summary}
   - [[2-values/README|Values & Priorities]] — {one-line summary}
   - [[3-mental-models/README|Mental Models & Frameworks]] — {one-line summary}
   - [[4-goals/README|Goals & Current Focus]] — {one-line summary}
   - [[5-decision-criteria/README|Decision Criteria]] — {one-line summary}
   - [[6-domain-expertise/README|Domain Expertise]] — {one-line summary}
   - [[7-heroes-influences/README|Heroes & Influences]] — {one-line summary}
   - [[8-open-questions/README|Open Questions & Tensions]] — {one-line summary}

   ## How to use this twin
   When Claude Code grounds an output against you, it reads this file first, then drills into whichever category/sub-theme is relevant. For maximum grounding, paste a specific sub-theme path into your next prompt: "Write in my voice, grounding against [[1-voice/em-dash-and-emphasis]] and [[3-mental-models/first-principles-thinking]]."
   ```

5. **Wikilink discipline (this is the prize):**
   - **Minimum 5 wikilinks** per category README — out to sub-themes, out to cross-category references, back to master MOC
   - **Minimum 2 wikilinks** per sub-theme file — to related sub-themes (same or different category) and back to the category MOC
   - **Every cited atomic note** → wikilink to the source note (the note exists as a real file in the vault — link to it)
   - This is what makes Obsidian's graph view light up. The MOCs become hub nodes; sub-themes become spoke nodes; atomic notes become the outer layer. Dense, browseable, navigable.

6. **Source citation discipline:**
   - Every claim in a sub-theme file should cite at least one source atomic note via wikilink
   - If a claim has no source, either find a source or drop the claim — don't fabricate

### Step 4.2 — Verify + report

After the synthesiser returns:
- Verify `03. Areas/Self/digital-twin/README.md` exists (if not, the agent was interrupted before the master MOC — note which categories completed and either re-spawn for just the master or rerun the full synthesis)
- Verify each of 8 category folders has a `README.md` + at least 2 sub-theme files
- Update progress.md: `phase_4_synthesis: complete`, `phase_5_cartographer: in-progress`
- Report:
   > "Phase 4 ✓ — Twin synthesized at `03. Areas/Self/digital-twin/`. {total files} files across 8 categories, all heavily wikilinked. Master MOC at `digital-twin/README.md` with {N} cross-cutting themes identified. Twin version: {N}.
   >
   > {if .obsidian/ detected in Phase 0:} Open your vault in Obsidian and switch to graph view (Cmd/Ctrl+G) — you'll see the twin rendered as a network. The dense hub in the middle is your master MOC.
   > {if .obsidian/ not detected:} Install Obsidian (obsidian.md → free), then 'Open folder as vault' and point it at this vault. Switch to graph view to see what we just built — the twin's structure becomes a literal map.
   >
   > Moving to Phase 5 — Cartographer pass that maps your WORK domains..."

═══════════════════════════════════════════════════════════
PHASE 5 — CARTOGRAPHER (map work domains)
═══════════════════════════════════════════════════════════

Print:
> "Phase 5 / 8 — Cartographer.
>
> Phase 4 captured WHO you are — voice, values, mental models, goals. Now we map WHAT YOU DO. I'll scan the atomic notes you produced in Phases 2 + 3 for recurring WORK DOMAINS (copywriting, investment, presentations, code, marketing — whatever actually shows up in your data) and walk you through each detected domain. For each, you decide: create as a new Area, attach as a subfolder under an existing Area, rename, or skip.
>
> Scanning now..."

### Step 5.1 — Load source atomic notes

Read all atomic notes from these paths, filtered to `#source/user-statement`, `#source/user-belief`, AND `#source/digital-twin-calibration`:

- `03. Areas/Self/atomic-notes/**` (chat history + calibration outputs)
- `04. Resources/AtomicNotes/imported/**` (generic reference from chat)
- `01. Inbox/atomic-notes-from-*/**` (inbox-fallback notes from Phase 2)
- `02. Projects/*/atomic-notes/**` (project-routed notes from Phase 2)
- `03. Areas/*/atomic-notes/**` (area-routed notes from Phase 2 — except those already under `Self/`)

Ignore `#source/model-statement` — model output isn't user signal.

If the user has thin data (no chat export, or only a partial calibration), warn:
> "Thin data warning: I'm working with {N} user-tagged atomic notes. Cartographer surfaces clusters with ≥10 notes per domain — you may see fewer or no domains detected. That's fine — you can re-run this pack after capturing more material."

### Step 5.2 — Cluster by work domain

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

### Step 5.3 — Write the detected domains file

Write `_System/active-installs/digital-twin/domains-detected.md`:

```yaml
---
phase: 5
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

Update progress.md: `phase_5.scan_complete: true`, `phase_5.domains_detected: {N}`, `phase_5.domains_total: {N}`, update `last_updated`.

Print:
> "Detected {N} work domains across {M} atomic notes:
> {numbered list: 1. {Domain} ({count} notes), 2. {Domain} ({count}), ...}
>
> Full detection report at `_System/active-installs/digital-twin/domains-detected.md`.
>
> Now walking through each one with you — say what to do per domain. Type 'quit' anytime; resume by saying 'continue' in a new session."

### Step 5.4 — Per-domain review loop

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

After EACH domain decision, write to `_System/active-installs/digital-twin/domains-confirmed.md`:

```yaml
---
phase: 5
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

Update progress.md: increment `phase_5.decisions_made`, update `last_updated`. Then move to the next domain.

If user types `quit`:
> "Decisions locked: {N} of {Total}. To resume, open Claude Code at your vault root and say 'continue' — I'll pick up at domain {N+1}."

When all domains reviewed:
> "All {N} domain decisions captured. Summary:
> - Create as Area: {count}
> - Add as subfolder: {count}
> - Skipped: {count}
>
> Building folder structure..."

### Step 5.5 — Create folder structure

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
tags: [type/area-readme, source/agent, source/cartographer]
created: {TODAY}
created_by: Digital Twin (Phase 5 Cartographer)
source_atomic_notes: {note_count}
---

# {Domain / Subfolder Name}

> {1-sentence description: what kind of work / notes live in this area}

## Sub-themes (detected from atomic notes)

{bullet list of sub-themes from Step 5.2}

## See also

- [[03. Areas/Self/digital-twin/6-domain-expertise/README|Domain Expertise (Digital Twin)]]
- [[03. Areas/Self/digital-twin/README|Master Digital Twin MOC]]
```

Skip any domain marked `skip` — don't create anything.

Update progress.md after each folder created: increment `phase_5.folders_created`. If a write fails, STOP and report.

### Step 5.6 — Re-route atomic notes

For each confirmed domain:
1. Find the atomic notes that belong to this domain (use the same clustering logic from Step 5.2, refined by user's confirmations from Step 5.4).
2. **Move (not copy)** those notes from their current location to the new destination:
   - If destination is a new Area: `03. Areas/{Domain}/atomic-notes/{original-source-tag}/{filename}`
   - If destination is a subfolder: `03. Areas/{Parent}/{Sub}/atomic-notes/{original-source-tag}/{filename}`
3. Preserve the `{speaker-tag}` subfolder structure (`user-statement/`, `user-belief/`, etc.)
4. After moving, search the vault for any `[[wikilinks]]` pointing to the old paths and update them to the new paths.

If two domains both claim a note (overlapping clusters), prefer the higher-frequency domain. Track these and mention to the user at the end as a "cross-domain note" report.

Persist progress.md after EACH batch of ~50 moves so resume can pick up mid-step. Increment `phase_5.notes_rerouted`.

### Step 5.7 — Cross-reference into digital-twin

Read the current `03. Areas/Self/digital-twin/6-domain-expertise/README.md` (Phase 4 wrote this).

Append (or update existing) a "Mapped Areas" section:

```markdown
## Mapped Areas (from Phase 5 Cartographer)

These are the work domains Cartographer detected and mapped on {TODAY}:

- [[03. Areas/{Domain1}/README|{Domain1}]] — {note count} atomic notes, sub-themes: {top 3}
- [[03. Areas/{Domain2}/README|{Domain2}]] — {note count} atomic notes, sub-themes: {top 3}
- ...

Each linked Area is a navigable hub for that domain. The twin's Domain Expertise section above is the SUMMARY; these Areas are the DEPTH.
```

### Step 5.8 — Archive and report

Archive Cartographer inputs/outputs for future re-runs:
- Move `_System/active-installs/digital-twin/domains-detected.md` → `02. Projects/Digital-Twin/_archive/cartographer-{TODAY}/domains-detected.md`
- Move `_System/active-installs/digital-twin/domains-confirmed.md` → `02. Projects/Digital-Twin/_archive/cartographer-{TODAY}/domains-confirmed.md`

Update progress.md: `phase_5_cartographer: complete`, `phase_6_wiki_drafts: in-progress`.

Report:
> "Phase 5 ✓ — Cartographer pass complete.
> - Domains detected: {N}
> - Areas created: {X}
> - Subfolders added: {Y}
> - Notes re-routed: {Z}
> - Cross-domain notes (assigned to highest-frequency domain): {count}
>
> Twin updated: `03. Areas/Self/digital-twin/6-domain-expertise/README.md` now lists your mapped Areas. The graph view in Obsidian (if installed) shows the twin connected to your work Areas as clusters.
>
> Moving to Phase 6 — wiki drafts..."

═══════════════════════════════════════════════════════════
PHASE 6 — MULTI-TOPIC WIKI DRAFTS (focused vault sweep)
═══════════════════════════════════════════════════════════

Print:
> "Phase 6 / 8 — Wiki Drafts.
>
> Second teaching moment: this is what the **Weekly Sweep** skill (ap-weekly-sweep) automates. Today I'm doing a focused sweep — distilling the major themes from your imported chats into multiple wiki articles you can review and approve. A future pack will automate this weekly.
>
> Compiling drafts now..."

### Step 6.1 — Identify wiki topics

Scan the synthesized twin folder + the topic-routed atomic notes (including the newly mapped Areas from Phase 5). Identify 5–15 major topics worth a standalone wiki article. Topic candidates surface organically — examples:

- "Who I Am" (always — distilled from the twin master README)
- "My Take on AI / LLMs"
- "How I Build / Operate"
- "My Faith Framework" (if applicable)
- "Parenting Philosophy" (if applicable)
- "How I Make Decisions"
- "Heroes & Influences"
- "What I'm Wrestling With"
- "My Voice in Writing"
- Domain-specific (often drawn from Phase 5 Areas): "Marketing Philosophy", "Content Strategy", "Investment Frame", etc.

A topic qualifies if there are ≥20 high-confidence atomic notes about it (across user-statement + user-belief + digital-twin-calibration sources).

### Step 6.2 — Draft each wiki article

For each identified topic, spawn a sub-agent (parallelisable — run them in waves of ~5) to draft a wiki article at `_System/wiki/drafts/{topic-slug}.md`:

```yaml
---
tags: [type/wiki, source/agent, source/vault-sweep, status/inbox]
compiled: {TODAY}
topic: "{topic name}"
from_sources:
  - "03. Areas/Self/digital-twin/{relevant category folders}"
  - "03. Areas/{relevant Cartographer Areas}/"
  - "{N} atomic notes from {paths}"
note_count: {N}
---

# {Topic name}

> {1-sentence framing}

## Core position
{2-3 paragraphs synthesising the user's stance}

## How it shows up
{bullet list with example citations}

## Tensions / open questions
{anything contradictory or unresolved in the source notes}

## Related
- [[digital-twin/{relevant categories}]]
- [[03. Areas/{relevant Cartographer Areas}]]
- [[other wiki drafts on related topics]]
```

### Step 6.3 — Update progress + report

- Update progress.md: `phase_6.topics_total: {N}`, `phase_6.drafts_complete: {N}`, `phase_6_wiki_drafts: complete`, `phase_7_register: in-progress`
- Report:
   > "Phase 6 ✓ — {N} wiki drafts compiled at `_System/wiki/drafts/`:
   > {list of drafts with link syntax}
   >
   > These are DRAFTS. Review at your pace using the wiki workflow (promote / correct and promote / reject). Each draft you promote moves to `_System/wiki/live/` and becomes canonical knowledge.
   >
   > Moving to Phase 7..."

(Don't force the user to review all drafts before Phase 7 — they can review later. The pack just delivers the drafts.)

═══════════════════════════════════════════════════════════
PHASE 7 — REGISTER PACK AS COMPLETE + CLEAN UP
═══════════════════════════════════════════════════════════

Print:
> "Phase 7 / 8 — Marking Digital Twin as complete..."

### Step 7.1 — Register in INSTALLED-PACKS.md

Check if `_System/INSTALLED-PACKS.md` exists. If not, create with this header:

```markdown
# Installed Expansion Packs

> Each capability you add to your vault registers here.

| Package | Title | Installed | Status | Adds |
|---|---|---|---|---|
| second-brain-setup | Second Brain Setup | {detect from CLAUDE.md created date OR ask user} | complete | five PARA folders, `_System/` rules and templates |
```

Append (or update if existing) Digital Twin row:

```
| digital-twin | Digital Twin | {TODAY} | complete | Project Digital Twin pipeline, atomic notes about you (routed by topic), 03. Areas/Self/digital-twin/ folder with 8 category subfolders, {Y} work-domain Areas mapped via Cartographer ({comma-separated names}), {N} wiki drafts, first-taste of inbox triage + weekly sweep |
```

### Step 7.2 — Clean up active install state

- Delete `_System/active-installs/digital-twin/` (the install is complete; resume state no longer needed)
- If `_System/active-installs/` is now empty, leave the empty directory (next pack will repopulate)
- Update `02. Projects/Digital-Twin/progress.md` to reflect full completion (`status: complete`)

### Step 7.3 — Report

> "Phase 7 ✓ — Digital Twin registered as complete. Install state cleaned up. Stack: 2 packs installed."

═══════════════════════════════════════════════════════════
PHASE 8 — CLOSEOUT
═══════════════════════════════════════════════════════════

Print:

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║              DIGITAL TWIN INSTALLED ✓            ║
║                                                  ║
╚══════════════════════════════════════════════════╝

What you unlocked:
  ✓ Project Digital Twin at 02. Projects/Digital-Twin/ (its own CLAUDE.md)
  ✓ {N} atomic notes routed across Self / Projects / Areas / Resources
  ✓ Your twin (WHO you are) lives at 03. Areas/Self/digital-twin/
        ├── 1-voice/         ({X} files)
        ├── 2-values/        ({X} files)
        ├── 3-mental-models/ ({X} files)
        ├── 4-goals/         ({X} files)
        ├── 5-decision-criteria/ ({X} files)
        ├── 6-domain-expertise/  ({X} files — now linked to your mapped Areas)
        ├── 7-heroes-influences/ ({X} files)
        └── 8-open-questions/    ({X} files)
  ✓ Your work domains (WHAT you do) mapped into Areas via Cartographer:
        {bullet list of created Areas + subfolders, with note counts}
  ✓ {N} wiki drafts at _System/wiki/drafts/ awaiting your review
  ✓ Manual inbox triage + weekly sweep felt (see Triage Inbox and Weekly Sweep)

What's next:
  - Browse your twin folder. There's more in there than you think.
  - Browse your mapped Areas — each one is a navigable hub with its own atomic-notes/ ready to grow.
  - Open the vault in Obsidian and switch to graph view (Cmd/Ctrl+G).
    If you haven't installed Obsidian yet: download from obsidian.md (free), open it,
    click 'Open folder as vault', point at this vault folder. Done — the graph view
    will render the twin you just built as a navigable network, branching out into
    your mapped work Areas as connected clusters. The dense hub is your master MOC;
    the spokes are your sub-themes; the outer layer is every atomic note feeding the
    synthesis.
  - Review the wiki drafts at your pace. Promote / correct / reject each.
  - Test the twin: ask me "draft me a paragraph in my voice about X, grounding against
    [[1-voice/README]]" — I'll ground in the relevant twin files.
  - Test a domain: ask me "draft me a {domain} piece in my voice, grounded against
    03. Areas/{Domain}/" — it'll ground against that domain's notes specifically.

Future packs (coming):
  Triage Inbox (ap-triage-inbox) — adds daily routing on top of this foundation
  More packs to come — each one stacks on what's already installed

Re-run this pack any time: re-paste setup-digital-twin V2.md.
(If you quit early next time, just say "continue" — resume state is on disk.)
```

═══════════════════════════════════════════════════════════
RESUME MECHANIC (how it actually works)
═══════════════════════════════════════════════════════════

User quits mid-install. Later, in a NEW Claude Code session:

1. User opens Claude Code at vault root
2. User types: "continue" (or "where did I leave off", or "resume my install")
3. Claude auto-loads vault root `CLAUDE.md`
4. CLAUDE.md's `## Active Installs` section instructs Claude to check `_System/active-installs/`
5. Claude finds `digital-twin/`, reads `progress.md` (current phase status) and `snapshot.md` (full original prompt)
6. Claude announces: "Found active install: Digital Twin. Last completed: Phase {N}. Resume from Phase {N+1}?"
7. User confirms → Claude re-executes the snapshot prompt's logic, skipping completed phases (using progress.md to know what's done)

The user never has to re-paste anything.

═══════════════════════════════════════════════════════════
SAFEGUARDS
═══════════════════════════════════════════════════════════

- **Pre-flight is non-negotiable.** Don't proceed past Phase 0 if the base vault isn't installed.
- **Persist before progress** in EVERY phase. Each chunk in Phase 2 commits before the next. Each Q+A in Phase 3 locks before the next. Each category in Phase 4 writes before the next agent returns. Each domain decision in Phase 5 commits before the next; each batch of note moves in Step 5.6 commits before the next. Each wiki draft in Phase 6 commits before the next.
- **Compaction-resistant.** State lives in `_System/active-installs/digital-twin/` + `02. Projects/Digital-Twin/` + `03. Areas/Self/digital-twin/` + Cartographer-created Areas, NOT in this conversation. Resume = open new session, say "continue."
- **Idempotent.** Re-running the pack from scratch detects existing state and offers to resume rather than overwriting.
- **PII.** Phase 2 flags sensitive data (passwords, full card numbers, SSNs, full home addresses, sensitive medical details) and does NOT extract those notes. Surface the list at end of Phase 2 for user review.
- **Never confuse model output with user voice.** Synthesis (Phase 4) and Cartographer clustering (Phase 5) both ignore `#source/model-statement` for belief/domain inference. Only user-tagged sources count.
- **Don't fabricate.** Phase 3 candidate answers come from the vault only. Phase 5 detection only surfaces clusters with ≥10 notes. If the vault has thin data, surface fewer domains — never invent them.
- **MOVE, don't COPY** in Step 5.6. Atomic notes belong in ONE place. Update wikilinks after moves.
- **User decides per domain.** Phase 5 is interactive — no autonomous folder creation. If user types 'skip' for a domain, that domain's notes stay where they are.

═══════════════════════════════════════════════════════════

End of prompt. Run Phase 0 now: check pre-flight, auto-detect chat export, report, wait for "go."
