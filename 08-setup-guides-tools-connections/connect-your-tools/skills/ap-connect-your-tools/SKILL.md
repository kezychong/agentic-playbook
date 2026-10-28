---
name: ap-connect-your-tools
description: "List every tool the owner uses across marketing, sales, operations, fulfilment and finance, pick each tool's read route (connector, plugin, MCP, API/CLI, WhatsApp Web, browser) and connect what can be connected. Use for \"list my tools\", \"pick the route for each of my tools\" or \"show my tools table\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. Drag it onto your brain folder, then tell Hermes: Read ap-connect-your-tools.md in my brain folder and list my tools.

# Connect Your Tools: list every tool, pick its route, connect it

**If you are Claude Code on the member's laptop, stop here.** This pack is for Hermes on the member's box. Tell the member in one line: "This one is for Hermes: drag it onto your brain folder, then in the Hermes app say: Read ap-connect-your-tools.md in my brain folder and list my tools." Do nothing else with this file.

**For Hermes.** The member dragged this file into their brain folder. Today you and the member list **every** tool they use, pillar by pillar (marketing, sales, operations, fulfilment, finance and admin), because listing them is how you both find out how each one can reach the brain. Then, for each tool, you check what it offers today, follow the flowchart below to pick its route, connect every tool that has a Hermes connector, a Hermes plugin or an MCP, and end with one table: tool, route, status. All of this is for the Capture bot, which only reads, so read-only access is enough for every tool. (Later, for the chief of staff, we find which of these tools need API or write access so it can act, not just read. Not today.) Keys go in through Claude Code on the laptop (the ap-add-a-key skill). The Connect to Capture skill then connects WhatsApp and joins every tool to the nightly capture.

## The member's sentences

| Part | The member says | You do |
|---|---|---|
| 1 | Read ap-connect-your-tools.md in my brain folder and list my tools. | Parts A and B |
| 2 | Pick the route for each of my tools and connect the MCPs. | Parts C and D |
| 3 | Show my tools table. | Part E |
| any | Add [tool] to my tools list. | That one tool through Parts B to D, then read its row back |

## Rules for this pack

- Keep this pack: move this file into `_System/packs/` (replace an older copy) and add one line under `## Packs you have` in AGENTS.md naming the sentences above and this file.
- **Never ask for, show, store or repeat a key, password or token.** If the member pastes one in chat, tell them in one line to make a new one in that tool (the pasted one is now in a chat log), and that keys go in only through Claude Code: "Add a key for [tool]."
- Ask only what the brain does not already answer. Read first, ask second.
- Report in plain words, no file paths unless asked. If stuck: "Record the failing step without secrets and consult your host support documentation."

## Part A: read what the brain already knows

Read the about-me note, the Digital Twin notes in `07. World Model/digital-twin/`, `_System/brain-map.md`, and anything in the brain that names a tool. Make a first list from that alone.

## Part B: list every tool, pillar by pillar

Sort the first list into the five pillars of the business and show it to the member. The kinds and example tools below only jog the member's memory; list the member's own tools, and add a kind when theirs do not fit:

| Pillar | Kind | Example tools |
|---|---|---|
| Marketing | Paid ads | Meta Ads, Google Ads, TikTok Ads |
| Marketing | Content | Instagram, YouTube, TikTok, LinkedIn |
| Marketing | Email | ActiveCampaign, Mailchimp, Kit |
| Marketing | DMs | ManyChat |
| Marketing | Site and funnels | ClickFunnels, WordPress, Webflow |
| Marketing | Numbers | Google Analytics, Meta Pixel |
| Sales | CRM | GoHighLevel (GHL), HubSpot, Pipedrive |
| Sales | Bookings | Calendly, GHL calendars |
| Sales | Sales calls | Zoom, Google Meet, Fathom |
| Sales | Checkout | Stripe, PayPal |
| Sales | Proposals | PandaDoc, DocuSign |
| Operations | Projects | Asana, ClickUp, Trello, Notion |
| Operations | Workspace | Google Workspace, Microsoft 365 |
| Operations | Databases | Airtable, Notion, Google Sheets |
| Operations | Team chat | Slack, Teams, Telegram |
| Operations | Files | Google Drive, Dropbox |
| Operations | Automations | Zapier, Make |
| Fulfilment | Client chat | WhatsApp, Telegram, email |
| Fulfilment | Client calls | Zoom, Google Meet |
| Fulfilment | Courses | Skool, Kajabi, Teachable |
| Fulfilment | Support | Intercom, Zendesk, a help inbox |
| Fulfilment | Delivery | the member's own tools of the trade |
| Finance and admin | Books | Xero, QuickBooks |
| Finance and admin | Invoices | Xero, QuickBooks, Stripe |
| Finance and admin | Payroll and HR | Gusto, Deel, a local payroll tool |
| Finance and admin | Expenses | Dext, Expensify |
| Finance and admin | Contracts | DocuSign, PandaDoc |

For Meta Ads and Instagram, check the system user route (Meta Business settings) when you pick the route in Part C, and walk the member through it step by step.

Ask in one message: "Here are the tools I found, by pillar. Go down each pillar: which other tools do you use, even ones you open only once a week? For each, what lives there that your brain should know?" Wait for one reply.

Write `_System/tools-list.md` with the columns `Tool | Pillar | Kind | What lives there | Route | Why this route | Status` (Route and Why empty for now, Status `not checked`). Add one line to AGENTS.md `## Hermes`: "The member's tools list is `_System/tools-list.md`; keep its Route and Status columns current." Names only: never a key in this file.

Report: "I listed [n] tools across the five pillars. Next, say: Pick the route for each of my tools and connect the MCPs."

## Part C: pick each tool's route (the flowchart)

What a tool offers changes every few weeks, so check each tool **today**. Never decide from memory. The Capture bot only reads, so a route counts when it can read what lives there. For each tool, in this order:

1. **Is there a Hermes connector for it?** Connectors are the apps listed in the Hermes app under Capabilities, then Connectors (on this box, `hermes mcp catalog` lists the catalog ones). If the tool is there and can read the data the member named for this tool: Route = `connector`. The member turns it on there and signs in.
2. **No connector: is there a Hermes plugin for it?** Run `hermes plugins search <tool>` on this box (and `hermes plugins show <name>` for a hit). It counts only if the plugin can read the data the member named for this tool; a plugin that only sends, or does something else, does not count. Yes: Route = `plugin`. Few tools have one yet; checking is quick.
3. **No plugin: on the tool's own website and developer docs, is there an MCP that can read it?** (MCP is a ready-made plug for agents; prefer the tool maker's own. Also look in `hermes mcp catalog`, the MCPs Hermes installs in one step.) Yes: Route = `MCP`. Some MCPs are limited and show only part of the data: if it cannot reach what the member named, go on to 4.
4. **No MCP that reads it: does it have an API, or an official command-line tool (CLI), that can read it?** Yes: Route = `API` (it takes a key) or `CLI` (Hermes runs the tool's own program, which signs in through the browser or takes a key).
5. **None of these:** WhatsApp on a personal number: Route = `WhatsApp Web` (Hermes links it through WhatsApp Web on this box; the Connect to Capture skill sets it up). Any other tool: Route = `browser` (Hermes signs into the tool's own web page in its own browser and reads it there; also set up tomorrow).

Write the Route, and in Why this route one plain line plus what you checked (Connectors, the plugin search, or the tool's page). Where the answer depends on the member's plan or account type (for example a business account), ask them about all such tools in one message.

## Part D: connect every connector, plugin and MCP tool now

For each `connector` row: tell the member to open Capabilities, then Connectors in the Hermes app, turn the tool on and sign in; prove it by reading the newest item and telling the member its title.

For each `plugin` row: `hermes plugins install <name> --enable`, then follow the plugin's own setup (a sign-in link for the member, or a key: Status = `needs a key`). Prove it by reading the newest item and telling the member its title, not its content. Status = `connected`, or the error in one plain line.

For each `MCP` row:

1. **Add it to Hermes:** `hermes mcp install <name>` when the catalog lists it, otherwise `hermes mcp add <name> --url <the tool's official MCP address> --auth oauth`, or the way the tool's own MCP page says.
2. **The member signs in once, on the tool's own page.** The Hermes app shows a setup card with Open in browser, or you give the member the sign-in link. The member signs in and allows access there; a password never goes into the chat. On a box with no screen, follow what the card says about the callback (open the link on the laptop, or paste the address the browser lands on back into the card).
3. **Let the Capture bot use it too,** because its nightly capture (Connect to Capture) reads this tool. If that needs a second sign-in under the Capture bot's profile, do it now, in the same sitting.
4. **Prove it:** `hermes mcp test <name>`, then read the newest item and tell the member its title, not its content.
5. Status = `connected`, or the error in one plain line.

For each `CLI` row that signs in through the browser: install the tool's official CLI, start its sign-in, give the member the link, prove one read the same way, Status = `connected`.

For each `API` row, and each CLI that takes a key: Status = `needs a key`. For each `WhatsApp Web` or `browser` row: Status = `Connect to Capture`.

Report one line per tool, then: "Next, in Claude Code on your laptop: make the ap-add-a-key skill, then say Add a key for [tool] for each tool marked needs a key. Keys never go through me."

## Part E: "Show my tools table."

For each `needs a key` row: read the names-only key list Claude Code keeps in the brain (`_System/KEY_LIST.md`), and check the key's name is in the locked drawer without reading a value: `grep -c '^NAME=' ~/.hermes/.env`, printing only the count. Never open `~/.hermes/.env` to read values. Where the key is in place, prove one read through the tool's API or CLI, then Status = `connected`.

Update `_System/tools-list.md`, then show the member the table in chat:

| Tool | Route | Status |
|---|---|---|

Status is one of `connected`, `needs a key`, `needs your sign-in`, `Connect to Capture`, or the error in one plain line.

## Report back

1. "Your [n] tools are listed by pillar. [n] connect by connector, [n] by plugin, [n] by MCP, [n] by API or CLI, [n] in Connect to Capture next (WhatsApp and any web-page-only tool)."
2. The table: tool, route, status.
3. "Next, Connect to Capture connects your WhatsApp[ and [web-page tools]], and every tool joins your nightly capture."
