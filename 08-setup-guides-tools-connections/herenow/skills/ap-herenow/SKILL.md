---
name: ap-herenow
description: "Set up a page-hosting account (here.now is the example) and, on explicit approval each time, publish a local HTML page as a link. Use for \"set up page sharing\", \"publish that page and send me the link\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Original starter method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# here.now Publishing

Publishing makes a page reachable by anyone with the link. Treat every publish as an outward-facing action: show the owner the page and what it contains, get a yes for that page, then publish.

## Set up once

1. The owner signs up at the hosting service (here.now is the worked example: an agent-friendly host that turns one HTML file into a link). Without an account, here.now links expire after about a day; with an API key they stay.
2. The owner creates an API key there and **copies** it. You store it with the Add a Key skill (`HERENOW_API_KEY` or the name the service's own skill expects). Never ask for it in chat.
3. If the service publishes an official agent skill, install that official skill after the owner approves it. Do not copy a third-party skill into this collection.
4. A custom domain usually needs a paid plan. Ask before any upgrade.

## Each publish

1. Name the exact file and summarise what is on the page in one or two lines. Check it holds no private data, keys, client names or anything the owner would not post publicly.
2. Ask: "Publish this page as a link?" Wait for yes.
3. Publish with the service's own tool, then send the link where the owner asked (for example their Telegram room).
4. Record the link, the file and the date in the owner's notes, so it can be removed later.

## Remove

On request, delete the published page with the service's own tool and confirm it no longer opens. Deleting a page is a separate approval.
