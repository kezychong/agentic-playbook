---
stage: draft
---
# NEEDS_REPAIR: landing-page
Same-agent review; this is not an independent fresh-context check.
A fresh session or a different model is recommended for an independent review.
Date: 2026-09-05
Brief: `brief.md`; deliverable: `landing-page.md`.
Practice save choice: beside the artifact; short summary: yes.
These practice choices do not fill the member's blank settings.

The draft meets the heading requirement but lacks the requested button label.

## Named checks
Working folder: `references/example/` inside this skill folder.
Command: `grep -nFx '# Fresh bread, ready daily' landing-page.md`
Exit code: 0. Actual stdout:
```text
1:# Fresh bread, ready daily
```
Stderr: empty.
Command: `grep -nFx '[Reserve a loaf]' landing-page.md`
Exit code: 1. Actual stdout: empty. Actual stderr: empty.

## Criteria
| ID | Requirement | Status | Verified evidence | Severity |
|---|---|---|---|---|
| C1 | Exact heading, brief.md:3 | MET | landing-page.md:1; heading check exit 0 above | None |
| C2 | Exact button label, brief.md:4 | NOT_MET | landing-page.md:3 says `[Learn more]`; label check exit 1 | must-fix |

The brief requires both checks to exit 0 before PASS (brief.md:9).
One required detail is missing; the page draft itself exists.

## Could not verify
None within the brief's scope.
Design, publication, and live behavior are excluded by brief.md:5.

## Drift list
- C2, must-fix. Brief: `brief.md:4`. Affected file: `landing-page.md:3`.
  Expected: `[Reserve a loaf]`. Actual: `[Learn more]`.
  Evidence: the exact-label check above exits 1 with no output.
  Repair: change the button label to the requested words.
  Recheck: run `grep -nFx '[Reserve a loaf]' landing-page.md` from this folder.
  It must exit 0 and print `3:[Reserve a loaf]` if the line stays in place.
  Run the heading check again to confirm C1 still passes.

Saved verdict: `references/example/JUDGE-2026-09-05-landing-page.md`.
Chat summary: NEEDS REPAIR. The heading passes; the requested button label is missing.
