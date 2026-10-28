> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.


# Troubleshooting

## Meta Account Not Visible
- Confirm the official Meta connector is used.
- Confirm the browser login used the right Meta account.
- Confirm the member has access to the ad account and Page.
- Stay read-only until visibility works.

## Numbers Look Wrong
- Check date range.
- Check level: use ad-set or ad level for cost-per-result decisions.
- Check the conversion action being counted.
- Compare tracker status before recommending action.

## Tracker Cannot Be Read
- Ask for the tracker source and tab/table label.
- Read headers first.
- Do not write rows.
- Use ap-tracker-sheet-review to create a dry-run update only.

## Creative JSON Cannot Be Updated
- Confirm the JSON source/path is available.
- Confirm every creative has a stable creative ID.
- Parse the JSON before proposing changes.
- Do not edit by fuzzy creative name.
- Use ap-tracker-and-creative-json-update to create a dry-run packet only.

## Launch Request Is Unsafe
- Use ap-approval-gated-actions.
- Refuse unapproved platform writes and live action.
- Ask for the exact approval sentence.

## New Campaign Creation Is Blocked
- Use ap-paused-launch-planner.
- Ask the owner to approve one existing source campaign to duplicate.
- Keep the duplicated campaign and child objects paused.
- Rename and edit only approved fields.
- Ask for separate approval before activation or unpause.

## Creative Is Failing QA
- Use ap-creative-quality-gate.
- Fix mobile readability first.
- Remove fake UI, unsupported claims, and extra ideas.

<!-- Agentic Playbook — by Kezy -->
