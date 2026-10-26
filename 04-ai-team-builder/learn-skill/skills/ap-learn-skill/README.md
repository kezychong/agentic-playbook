# Learn Skill

Agentic Playbook — **by Kezy**

Package a proven workflow as a reusable local skill.

Start with [the complete workflow](SKILL.md). This adapts supplied source material;
Kezy is the repackage maintainer. Version 0.1.0; runtime untested.

## Prerequisites
An existing skill-capable host, a writable draft folder and the task inputs described in the workflow.
Only allow the files and integrations needed for this task. No account is needed for a fictional rehearsal.
Copy the complete folder, including references, templates and scripts when present.
See [manual host setup](../../../../08-setup-guides-tools-connections/manual-setup.md).

## Example trigger
“Use ap-learn-skill with fictional Company A inputs. Describe missing inputs first, then produce a local draft. Do not install, connect, send or publish.”

## Output
A scoped brief, staged workflow or evidence-based review. Read SKILL.md for the full output contract.

## Limits
Bundled scripts are unexecuted source assets. No runtime, model access, visual rendering or integration
has been tested in this repackage. Missing inputs remain unknown. Live changes need explicit approval.

## Optional source helper
`scripts/skill_tools.py` preserves list, archive, archive-inspection and staged-copy operations.
It requires Python 3.9+ and an explicit approved `--workspace`; it does not read home profiles or
credential stores. The workspace contains skills/, inbox/, exports/ and backups/. Its install command
copies only within that workspace and requires `--approve-install`; host activation is a separate
manual step. Shared archives require human review acknowledgment. Pattern scans are incomplete.
The helper was syntax-checked only, not executed. Review it before use and never point it at a
private live profile merely to list skills. See its docstring for the preserved command interface.

## Optional companion skills
`ap-orchestrator-astra`, `ap-orchestrator-opus`. If absent, report that limitation and use this skill's own method; do not claim the companion ran. These are not required for local discovery.
