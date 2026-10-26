# The creative memory tracker

This file is for the agent. The owner never edits the tracker by hand.

## What it is

A JSON file holding one profile per ad. It is the account's memory of what has been run, what won, and what already burned out.

It exists because the ad platform will not show you this. You can see numbers next to an ad name, but you cannot scan fifty image ads and remember which headline was on which one, or which angle you already tried eight months ago. The tracker holds that outside the platform, in the owner's own folder, where it survives.

## Why it matters

Without it, every creative run starts from zero. The same angle gets re-run after it already died, and a winner that is sitting right there gets ignored.

With it, two things happen every run:

- **Read before you brief.** Winners to lean into. Burned angles to skip. Headlines already used, so nothing gets repeated by accident.
- **Append after you generate.** Every new batch becomes memory for the next run. This is what makes run three better than run one.

## Finding it

Look in the owner's project folder for an existing tracker JSON before you create anything. If one exists, use it. If you are not sure where their work lives, ask them one plain question: "Which folder do you keep this account's work in?"

**If a tracker already exists, extend it. Never start a second one.** Match the keys it already uses, even if they are named differently from the ones below. Two trackers with two shapes is worse than no tracker, because now nobody knows which one is true.

If there is no tracker, create one with the shape below, fill it from the ad profiles you wrote in step 3, and tell the owner in one sentence that it exists and what it is for.

## The shape

```json
{
  "id": "120xxxxxxxxxx",
  "account": "the ad account name",
  "awareness": "unaware | problem | solution | product | most",
  "concept": "short concept label",
  "variation": "1 of 5",
  "headline": "the on-image or ad headline",
  "primary_text": "the ad's primary text",
  "visual": "written description of what is on screen",
  "date_created": "YYYY-MM-DD",
  "status": "new | running | winner | retired",
  "notes": "where it came from, what it tested, how it performed"
}
```

Optional key: `"visual_style": "simple-photo | quote-card | screenshot | diagram | designed"`, so the next brief can see which looks already ran.

Useful extras when the ad is a video, added as more keys on the same profile: `format`, `length_seconds`, `hook`, `script`, `sound`.

## What the statuses mean

- **new**: generated, not launched yet.
- **running**: live in the account right now.
- **winner**: produced results at a cost the owner is happy with. Say the number in `notes`.
- **retired**: switched off. Say why in `notes`, because "retired because it never worked" and "retired because it worked for four months then died" lead to opposite decisions next time.

Keep statuses current as ads run. A tracker where everything says "new" is a list, not a memory.

## Reading it before the brief

1. Load the tracker.
2. Filter to this account.
3. Pull out: winning angles, headlines and hooks already used, which awareness level each past ad spoke to, and anything marked retired.
4. Feed all of that into the brief. Lean into what won. Do not re-run what died. Do not repeat a headline that already ran unless you are deliberately re-testing it, and say so when you are.

## Appending after generation

After a batch is produced, add one profile per new ad. Fifty new creatives means fifty profiles.

- One profile per ad, never one per concept. The five variations of a concept are five ads.
- `status` starts at `new`.
- `notes` records what the variation was testing, in one line. "Same script, hook changed to the question version" is worth more later than "variation 3".
- Fill `date_created` so the next run can tell a three week old angle from a two year old one.

## Discipline

- Match the existing schema. Do not fork a second format.
- The tracker is memory, not strategy. It tells you what happened. The awareness levels and the account's own performance tell you what to do next.
- Never delete a profile. Retire it instead. A dead ad is evidence.
- Keep it in the owner's folder, next to their other work, so it is still there next quarter.
