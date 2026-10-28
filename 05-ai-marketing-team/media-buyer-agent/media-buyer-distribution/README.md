
# Media Buyer Agent Distribution v1

GitHub install after access is granted:

```bash
```

Local install:

```bash
hermes profile install /path/to/media-buyer-distribution --name media-buyer --alias
```

After install:
1. Confirm the member's Hermes Chief of Staff already works through Codex on this device.
2. If Hermes reports missing model auth, run `hermes model` and choose the Codex/OpenAI Codex provider.
3. Connect Meta's hosted Ads connector: https://mcp.facebook.com/ads
4. Start read-only.
5. Treat paused campaign/ad-set/ad creation as a platform write that needs approval.
6. Connect or provide the member-owned tracker and creative JSON source.
7. Run QA-SCENARIOS.md before real spend.

This distribution contains no live workspace history, secrets, sessions, logs, memories, client
tracker data, or Meta account IDs.

## Skills (Agentic Playbook layout)

The nine canonical skill folders live once, at [`../skills/`](../skills/), not inside this template. Before any approved profile install, stage a copy of this folder and copy the nine skill folders into its `skills/` directory. Verify the host's current profile schema first. Nothing here installs or connects by itself.
