# Manual installation note — Agentic Playbook, by Kezy

This is documentation, not an instruction to install on load. Review the complete folder and
[manual host guide](../../../../08-setup-guides-tools-connections/manual-setup.md). Obtain approval
before changing a live host. Older app-specific steps below are conditional on current host
support; no installation or integration has been tested. Preserve existing versions.

# Install — Challenge Offer Architect

## What this is

A skill that walks you through designing a **challenge offer** — a low-priced, time-boxed offer with a fixed cohort start date that packages a DIY program with real accountability — and produces every asset for the offer itself. It is designed for **Claude Code or Codex**; verify discovery in your host.

This builds the offer. It does not build the landing page or launch emails that sell it — that's a separate job.

Not sure how to install any of this? Just paste this folder's location to your AI assistant and say "install this skill for me."

## Install (about 2 minutes)

1. **Unzip** this folder.
2. **Copy the whole `ap-challenge-offer-creation/` folder** into your Claude Code skills folder:
   - `~/.claude/skills/ap-challenge-offer-creation/`
   - (On Windows: `C:\Users\<you>\.claude\skills\ap-challenge-offer-creation\`)
   - Keep the structure intact — `SKILL.md` must sit at the top of the folder, with `references/` beside it.
3. **Restart Claude Code** (or open a new session) so it picks up the new skill.

That's it. No accounts, no keys, nothing to configure.

## How to use it

Just describe what you want in plain language. The skill triggers on things like:

- "Help me create a challenge offer."
- "My calendar is full and I can't take more 1:1 clients — what do I do?"
- "Turn my program into a challenge."
- "I need a leveraged offer."
- "My online program isn't getting people to finish."

You don't have to name the skill. Claude will recognize the situation and start the intake.

## What you'll get

Working in your own project folder, the skill helps you produce:

- `audience.md` and `offer.md` — reusable descriptions of who you serve and what you sell.
- A **day-by-day challenge outline**.
- A **launch content calendar** for the pre-launch runway.
- A **registration-page brief** — a handoff spec for whoever builds that page, not a finished page.
- **Daily prompts** (the one action + community check-in per day).
- An **end-of-challenge upsell pitch outline**.

## A note on duration

There's no required length. 30 days, 4 weeks, 6 weeks all work — the skill asks what fits your outcome and your audience's stamina, then designs around that.

## A note on expectations

A challenge is a *launch* mechanism. It monetizes an audience you already have — it doesn't create one from scratch. If your reach is small today, the skill will tell you so honestly and help you plan accordingly. That's by design.

## Tips

- **Give it context.** The more it knows about your niche, past results, and current offers, the sharper the output. Point it at your `audience.md` and `offer.md` every time.
- **Keep a folder per challenge.** Drop your results in after each launch. Next time, the skill can learn from what worked.
