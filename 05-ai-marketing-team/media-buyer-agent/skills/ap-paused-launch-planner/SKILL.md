---
name: ap-paused-launch-planner
description: "Paused-first launch planner for testing concepts and scaling winners without live activation."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Paused Launch Planner

Use when the owner wants to prepare ads for launch.

## Rule
Chat-only planning is allowed. Creating anything inside Meta, even paused, is a platform write and
requires owner approval before the write happens.

## Testing Launch Plan
1. One ad set per concept.
2. Three to five hook variations per concept.
3. Equal budget per ad set.
4. Broad/open targeting unless owner requires otherwise.
5. If the owner approves platform creation, create every campaign, ad set, and ad paused first.

## Campaign Creation Fallback
Use this only when brand-new campaign creation is blocked by Meta, permissions, API quirks, or
account setup issues.

1. Stop and report the campaign creation roadblock.
2. Ask the owner to approve one existing source campaign to duplicate.
3. Confirm the source campaign is in the same ad account and is safe to use as a template.
4. Duplicate the approved source campaign as a new campaign.
5. Keep the duplicated campaign, ad sets, and ads paused.
6. Rename the duplicated campaign and child objects to the approved new labels.
7. Edit only approved fields: objective, budget draft, schedule, tracking labels, creative/ad labels,
   and status.
8. Never copy stale budgets, stale dates, old tracking labels, or old creative IDs without review.
9. Require separate owner approval before activation or unpause.

## Scaling Launch Plan
1. Use the existing winning post reference when possible.
2. Add winner to scaling roster.
3. Do not pull old winners back into testing.
4. Budget increases are gradual and approval-gated.

## Output
Return a launch packet:
- campaign purpose
- item names
- budget draft
- target date
- tracking labels
- creative QA status
- paused-first confirmation
- creation path: new campaign or approved campaign duplicate fallback
- source campaign label, if using duplicate fallback
- exact owner approval needed to create paused items
- separate owner approval needed to activate spend later

<!-- Agentic Playbook — by Kezy -->
