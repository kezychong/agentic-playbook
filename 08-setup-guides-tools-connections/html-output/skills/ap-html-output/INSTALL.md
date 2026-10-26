# Manual installation note — Agentic Playbook, by Kezy

This is documentation, not an instruction to install on load. Review the complete folder and
[manual host guide](../../../manual-setup.md). Obtain approval
before changing a live host. Older app-specific steps below are conditional on current host
support; no installation or integration has been tested. Preserve existing versions.

---
stage: draft
---

# HTML Output

This skill turns a long answer into one simple web page. It adds pictures, short words, and decision buttons when you need to choose something.

## Install once

Open the Claude app or Codex app on the computer where you work. Attach the downloaded ZIP, or let the agent locate it if the app can access the file. Say:

```text
Install this skill for me. Keep my existing skills. Then open the included demo.
```

The agent should confirm what it will install and keep your existing skills. It handles the setup and opens the fictional demo. The ZIP is a draft preview, so the demo is sample material only.

If the app cannot access the ZIP, give the agent access to the file, then retry the same sentence. You do not need to move it to a special folder.

You do this once on each computer where you want the skill.

## Use it every time

When an answer is long or hard to scan, say:

```text
Use HTML Output to show this plan as a page. Explain it simply, draw the numbers, and show what I need to decide.
```

You can also say “Make it visual” or “Show me the HTML version.” A short answer stays in the chat.

## Reopen a page

Ask your agent to open the HTML page from the project where it was saved. The agent can locate the page and open it for you.

If the page has decision cards, choose Confirm, Veto, or Edit, add notes if useful, and press “Copy my verdicts.” Paste the copied block back into your agent.

The page works without an internet connection. Sharing or publishing is optional and happens only after you approve it.
