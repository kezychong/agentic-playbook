> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

# Tracker And Creative JSON Template

Use this as the generic setup guide for a member-owned tracker. Do not add real client names, sheet
IDs, account IDs, or private values to the shared pack.

## Tracker Columns

Recommended columns:

- row_id
- creative_id
- creative_name
- campaign_label
- ad_set_label
- ad_label
- status
- launch_date
- end_date
- spend
- results
- cost_per_result
- action
- notes
- frozen

## Creative JSON Requirements

Each creative should have one JSON record with:

- `creative_id`
- `name`
- `concept`
- `status`
- `tracker.source`
- `tracker.tab`
- `tracker.row_id`
- `qa.decision`
- `qa.notes`
- `performance.date_range`
- `performance.spend`
- `performance.results`
- `performance.cost_per_result`
- `decision.recommended_action`
- `decision.approved_action`
- `decision.approval_reference`
- `decision.updated_at`

## Update Rule

The agent prepares a dry-run packet first. It writes only after the owner approves the exact tracker
row, creative ID, and fields.


<!-- Agentic Playbook — by Kezy -->
