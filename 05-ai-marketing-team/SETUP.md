# Set up a draft marketing workspace

Agentic Playbook — by Kezy

1. Choose one skill from the [topic index](README.md) and read its README, SKILL and INSTALL files. Preserve the entire folder when copying it to the host’s documented discovery location. See the collection [host setup guides](../08-setup-guides-tools-connections/README.md). Host discovery is not live-tested here.
2. Choose a separate working folder, such as `marketing-work/`. Copy [campaign intake](templates/campaign-intake.md) there and define the permitted source list. Do not scan a whole profile, mailbox or vault by default. Exclude secrets, private third-party material and client data that is not authorized.
3. Run the fictional text example first. Request a local draft only, with research, generators, accounts and schedules disabled. Confirm the correct skill loaded and that missing facts are reported as gaps.
4. Add capabilities only when needed. Text drafting needs a compatible host. Edit Pipeline needs Python and video/transcription dependencies. Carousel export needs Python, Playwright, Chromium and Pillow. The presentation checker needs Python/Playwright. Content OS dashboard and analytics need Python; optional research sends approved URLs/queries to external providers. Review each tool’s prerequisites before approving an install.
5. Before an account connection, agree the account identity, minimum read scope, date range, data sent to the host/provider and spending cap. Start with an authorized CSV/export if possible. The owner signs in directly and stores keys in secure local setup, never chat. Confirm revoke controls in the provider. No connector availability, free tier or price is guaranteed.
6. Keep research harvest and analytics reminders off until a manual run succeeds and the owner approves exact folders, timezone, cadence and limits. Content OS dashboard step buttons default to copy-and-paste; background agent execution is a separate opt-in. Browser closure alone may not stop its server.

## Update and removal

Back up a customized same-ID folder before replacing it; compare source version 0.1.0 and preserve local answers outside the package. Refresh the host and verify discovery. Removal requires approval: remove only the installed skill folder, stop approved local services, remove the specific schedules and revoke optional provider tokens separately. Keep drafts and user data unless separately asked to delete them. Do not claim deleting a skill revokes an external account.

## First-run acceptance

The sample should produce a draft with named sources, visible unknowns and no invented business results. A successful text sample does not establish video export, dashboard safety or live-account compatibility. Record the exact capability checked, date, inputs and observed output before claiming runtime success.
