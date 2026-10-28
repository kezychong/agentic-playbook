> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.


# Start Here - Media Buyer Agent v1

This pack installs a member-safe media buyer profile with practical operating skills.

## What It Can Do
- Verify Meta connector readiness.
- Review ad performance.
- Check tracker rows.
- Prepare approved tracker row and creative JSON updates.
- QA creative before launch.
- Plan paused-first launches.
- Refuse unsafe platform writes and live actions.
- Write weekly summaries.

## What The Member Supplies
- Their own Hermes runtime.
- Their existing Hermes Chief of Staff / Codex setup on this device.
- Their own Meta account access.
- Their own tracker or sheet.
- Their own creative JSON source, if they use one.
- Their offer, primary result type, and target cost per result.
- Their own ad budget and approval decisions.

## Model Guide
Default provider: Hermes OpenAI Codex.
The normal member setup reuses the same Codex-backed Hermes runtime that already runs Chief of Staff.
No separate Anthropic API token is required for the standard setup.
If Hermes says model auth is missing, run `hermes model` in Terminal and choose the Codex/OpenAI Codex provider before using the Media Buyer profile.

## Install From Local Folder
```bash
hermes profile install /path/to/media-buyer-distribution --name media-buyer --alias
```

Then follow QA-SCENARIOS.md before real spend.

Before the first review, complete onboarding-questionnaire.md so the agent knows what the ads sell,
what counts as a result, and the target cost per result. A result might be a sale, lead, booked call,
application, or another business-specific conversion.

Important: creating a paused campaign, ad set, or ad inside Meta is still a platform write. The agent
may plan it in chat, but it needs approval before writing anything into Meta.

Tracker and creative JSON writes also need approval. The agent can prepare a dry-run update packet
first, then write only the exact approved rows, creative IDs, and fields.

<!-- Agentic Playbook — by Kezy -->
