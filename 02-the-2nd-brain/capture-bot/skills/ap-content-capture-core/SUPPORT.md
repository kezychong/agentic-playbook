# Capture support bundle

Agentic Playbook — by Kezy

All original pack-level scripts, configuration, templates, examples and installation/repair methods live in this folder. The five extractor skills are canonical siblings. Run a documented helper command from the folder named by that method; do not assume the old ZIP root. In a selected host skill directory, the paths are `ap-content-capture-core/scripts/`, `ap-content-capture-core/config/` and `ap-content-capture-core/templates/`.

The optional `install.sh` expects this folder and all five extractor siblings. After reviewing and approving the destination, invoke it with `bash install.sh --approved "<host skill directory>"`. It refuses conflicts, copies complete folders, and performs no runtime checks, downloads, credential copying, scheduling or deletion. Resolve updates manually with backups. Helpers remain inside this core folder.

The nightly capture method is optional and disabled by default. Approve each source profile; use explicit --profile arguments. Raw exports belong outside the shared vault using the helper's --export-brain option. The retained legacy repair logic may report unresolved external links; preserve those blocks and review them rather than guessing a watermark.

The supplied tests and scripts are unexecuted source assets. No integration success is claimed.
