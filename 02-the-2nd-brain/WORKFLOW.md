# Capture whole sources; distill ideas later

Agentic Playbook — **by Kezy**

## 1. Set up the vault

[Second Brain Setup](second-brain-setup/skills/ap-second-brain-setup/SKILL.md) contains the full interview, PARA build, privacy gate, upgrade and resume procedures. Its templates/vault directory holds the actual rules, manifest, receipt ledger and note templates. Use the owner's chosen businesses and shelves. For an existing vault, check active schedules before proposing folder renames. Keep existing folder names if renaming would break jobs.

Install the four canonical helper folders alongside setup. They share the setup skill's included support templates, so the dependency group travels together. The supplied source targets Claude vault skills for one procedure; use the chosen host's documented location and verify discovery. Nothing here activates an autopilot.

## 2. Choose one capture route

[Content Capture Core](capture-bot/skills/ap-content-capture-core/SKILL.md) routes documents, articles, Reels, X posts and YouTube videos to their specific extractors. All pack-level scripts, configuration, templates and API guidance live inside the core folder. A media extractor depends on that folder being included. Commands in an extractor run from its skill folder, with shared helper paths pointing to ../ap-content-capture-core/.

One supplied source becomes one complete original note in 01. Inbox/agent-drops/. Preserve source metadata and uncertain names. Very long originals can live in 08. Sources/captures/ with a complete link from the note. That extra folder is a capture convention, created only when needed; it is not part of the five-folder PARA skeleton. A failed transcript is not a successful capture.

[Capture Router](capture-router/skills/ap-capture-router/SKILL.md) handles thoughts, tasks and decisions according to the configured notebook. [Capture Session](capture-session/skills/ap-capture-session/SKILL.md) first shows a small candidate list and records only approved durable lessons. Use actual accessible session history; if tool provenance is unavailable, say so rather than fabricating expressed-from entries.

[WhatsApp Capture](whatsapp-capture/skills/ap-whatsapp-capture/SKILL.md) is optional and separate. Reading a chat may clear unread badges and send read receipts. Agree the exact chat allowlist and that side effect before access. Do not enable its optional two-hour schedule during a sample.

## 3. Route, then distill

[Triage Inbox](second-brain-setup/skills/ap-triage-inbox/SKILL.md) checks sensitivity first, active work second, reference knowledge third. Unclear destinations remain in the Inbox. Record moves in WHERE-DID-IT-GO.md. [Distill](second-brain-setup/skills/ap-distill/SKILL.md) then creates separate atomic ideas linked to the intact source. This deliberate distinction preserves both evidence and findability.

[Import AI Exports](second-brain-setup/skills/ap-import-ai-exports/SKILL.md) processes approved exports in batches, creates one note per conversation, and tracks an index. Do not treat an AI memory summary as a confirmed fact about the owner. Private raw archives remain outside the vault.

## 4. Review weekly, manually first

[Weekly Sweep](second-brain-setup/skills/ap-weekly-sweep/SKILL.md) reports stale inbox items, orphan notes, routing gaps, distillation candidates and decisions due for review. Answered decisions may be updated with the owner's confirmed wording. Do not silently move the rest. Scheduling is optional and requires a separate approved setup.

## Layout compatibility

Some supplied methods refer to legacy 00. System, 07. World Model, Signals or AUTOMATIONS.md. These are runtime conventions, not files promised by the basic PARA template. Resolve them through the user's confirmed vault manifest; use _System for a new vault. If a needed runtime file does not exist, ask for its content or record it missing. Never invent an already-installed automation.
