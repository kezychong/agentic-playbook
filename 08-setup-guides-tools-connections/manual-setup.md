# Manual skill setup in an existing host

Agentic Playbook — by Kezy

These paths and discovery steps come from the supplied official documentation snapshots:
[Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills),
[Claude Code skills](https://code.claude.com/docs/en/skills), and
[Codex skills](https://learn.chatgpt.com/docs/build-skills).
They are documentation-sourced, not live-verified compatibility. No host runtime installation,
login, profile change, source script or integration was executed in this build.

## Choose and copy
1. Select one `skills/ap-name/` folder. Read README.md, SKILL.md and included scripts first.
   Read its catalog dependency list in the complete collection. Copy required companion skills
   too; optional absent skills must remain explicitly unavailable. Ordinary programs are separate prerequisites.
2. Choose a scope below. Confirm the destination and obtain approval to change a live host.
   Copy the **entire folder**, preserving references/, templates/, scripts/, agents/ and assets/
   when present. Do not copy only SKILL.md. Do not flatten files or run scripts while copying.
3. If that skill name already exists, compare versions and keep a rollback copy outside scanned
   skill directories. Do not silently overwrite custom settings. Keep one intended active version.

| Host | Local folder in the supplied official docs | Discovery / harmless invocation |
|---|---|---|
| Hermes | `~/.hermes/skills/ap-name/` for the default profile; verify the active profile's actual location | Inspect skills list, then `/ap-name` with fictional inputs |
| Claude Code | `.claude/skills/ap-name/` for project scope or `~/.claude/skills/ap-name/` for personal scope | Ask what skills are available, then `/ap-name` |
| Codex | `.agents/skills/ap-name/` in the working project or `~/.agents/skills/ap-name/` for user scope | Use `/skills` or `$ap-name`; restart if changes do not appear |

These are host-specific locations. Claude Code documentation does not prove that another Claude
app uses the same folders. Codex can discover changes automatically. Hermes may update available
skills on the next message; a fresh session also helps diagnose stale discovery. Verify the actual
loaded name and file path, not merely that copying succeeded.

## Harmless first run
Use `ap-html-output` with the fictional example in this topic. Ask for a local draft only, no
installation, browser automation, network, account access or publication. Inspect output and
record what was and was not exercised. For Finance, use the fictional manual dataset and no connector.
Scripts remain optional unexecuted assets until separately reviewed and explicitly run.

## Conflicts and troubleshooting
Check spelling and that name in frontmatter matches folder. Check SKILL.md is at folder root.
Confirm scope and active profile; a skill in the wrong profile is not installed for this session.
Hermes uses precedence across project, local and external locations. Codex does not merge equal
names and can display both. Resolve duplicate folders deliberately. Do not delete unknown versions.
Missing tools or models are real gaps: choose a supported configuration with approval or stop
that part. Do not install packages automatically to make discovery work.

## Updates and removal
Stage the new complete folder, compare changed methods and permissions, save the current version
outside discovery paths, then replace only the approved folder. Preserve user settings privately.
For removal, pause any separately approved schedules and remove or disable only the selected
installed skill after approval. Restart/recheck discovery. Revoke connections separately; removing
a skill does not revoke tokens, cancel subscriptions or erase retained source files.
