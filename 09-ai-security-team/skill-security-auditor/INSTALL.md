# Manual installation — Skill Security Auditor

Agentic Playbook — by Kezy Chong

[Use terms](USE-TERMS.md): retain the credit and terms. Personal/internal use only within the grant; external sharing, publication, sale or rebranding needs separate written permission. Independent third-party software rights remain separate.

**Status: prepared; engine not installed or runtime-tested.** This document describes a possible future copy of the adapter. No copy into Hermes, engine setup or scan is authorized by reading it.

## Install the adapter only, after approval

1. Read [SKILL.md](SKILL.md), the [guide](GUIDE.md), [engine interface](references/ENGINE-INTERFACE.md) and [approval/report contract](references/APPROVAL-AND-REPORT.md).
2. Identify the actual active host/profile and supported skill directory from the host's current documentation. For Hermes, resolve the active home/profile rather than assuming a default path. Do not modify any other profile. No runtime settings edit or service restart belongs to this installation.
3. Propose an **exact absolute destination** ending in `skill-security-auditor/`. Check both the path and existing discovered skill IDs, including nested category folders. A same-name skill elsewhere is also a conflict.
4. **On any name/path conflict, stop and wait for explicit approval.** Explain the differences and preserve personal edits; do not overwrite, merge, rename the existing skill or choose a different destination automatically. If an update is later approved, preserve a rollback copy outside host-discovered skill directories first.
5. With no conflict and explicit approval of the exact destination, copy this complete folder only: root `SKILL.md`, `README.md`, `INSTALL.md`, `GUIDE.md`, `USE-TERMS.md`, `PACKAGE.json` and both files under `references/`. No extra `skills/` nesting or `ap-` prefix is needed. Do not copy private engine source, provenance, reports or licences into the adapter. Do not execute anything while copying.
6. Verify the copied file inventory/content and use the host's read-only skill listing to check ID `skill-security-auditor` at the approved path. Loading should start nothing. If discovery is cached, report that condition and consult documentation; do not restart a gateway/service or alter settings.
7. Try the fictional planning-only prompt in [GUIDE.md](GUIDE.md). It should explain approval questions and stop, not open target files or run a scanner.

This preparation did not perform those installation steps. The package is macOS-oriented; copying it does not establish runtime compatibility on this or another platform.

## External engine preparation is a different approval

The local source directory documented in the interface is a private reference, not proof of an installed executable. This package contains no installer and authorizes no package-manager/dependency commands. If a user later wants a runnable engine, propose a separate bounded setup of the privately pinned source, retaining its original ownership, licence and notices. Record the actual verified executable outside the playbook. Do not use an unpinned latest release or an arbitrary global command.

Engine installation is not scan permission. Before the first scan, separately approve a staged target, enforceable limits and private outputs, and independently verify OS containment with all network denied. Without a supported already-verified sandbox and process-tree supervisor, **cannot run** is the correct outcome. Do not start a service/MCP host as an alternative.

## Update or remove deliberately

Stage future adapter versions, compare them and stop for approval at conflicts. Engine versions are separately pinned and require fresh interface review; do not silently reuse these instructions against changed software. Scan permission never carries over to a changed target version.

For removal, approve deleting only the exact installed adapter folder and verify discovery. Do not remove the private engine source, licence, reports or provenance as a side effect. There are no schedules, hooks or services in this package to remove.
