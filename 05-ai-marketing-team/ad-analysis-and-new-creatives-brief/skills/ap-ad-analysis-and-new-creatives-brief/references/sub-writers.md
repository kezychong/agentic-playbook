# Sub-writers

This file is for the agent. Load it only after the owner has approved the brief.

## What changes

One writer per approved concept, instead of you writing the whole batch in one pass. Each concept gets its own writer's voice, and the batch comes back faster.

## The cap

**Run the writers in parallel.** If this runtime or the member's plan throttles parallel agents, queue the rest and start each one as another finishes.

## What each writer gets

Paste the whole block below to each writer, with the placeholders filled in. A writer has no memory of the account, so nothing can be left implied.

```
You are writing one concept from an approved ad brief.

THE DECISION CARD (one screen):
<paste Part 0>

YOUR CONCEPT BLOCK from the brief:
<paste only this concept's block>

VISUAL FORMAT for this concept:
<simple or designed, and the palette and layout the other concepts already use, so you do not repeat them>

YOUR CONCEPT (this is the only one you write):
Concept name: <name>
Awareness level: <one of the five>
Angle: <one sentence>
Hook direction: <the hook from the brief, word for word>
Format: <image or video>
Length: <seconds, for video>
What it is testing: <one line>

HOOK AND BODY RULES FOR THIS AWARENESS LEVEL:
<paste the matching level block from creative-brief-template.md: the ad's job,
the hook emotion, the hook shapes that work, and how it is judged>

WINNERS TO ECHO (from the account, seen first hand):
<the relevant per-ad profiles that won, with their numbers>

BURNED ANGLES TO AVOID:
<the relevant retired or fatigued profiles, with the reason each died>

HEADLINES ALREADY USED (do not repeat any of these):
<the headline list pulled from the creative memory tracker>

Return exactly five variations of this concept. Change one thing at a time,
following the variation rule in the brief. Nothing else.
```

## What each writer returns

Exactly five variations. Each one carries all five of these, in this order:

1. **The hook.** The first three seconds of the video, or the on-image headline. Written word for word, never described.
2. **Primary text.** The ad copy that sits above the creative.
3. **Script or visual direction.** For video, the beats in order. For image, what is in the frame.
4. **Length.** In seconds for video.
5. **The generation ready prompt.** Complete on its own. Always states the length. Always says "no music" unless music is wanted for this ad. It has to obey the prompt rules in `generator-handoff.md`.

Anything short of five, or missing a field, goes back to that writer. Do not patch it yourself.

## Your pass after all writers return

Four things, in order:

1. **Collision check.** Read the batch hooks and headlines side by side. Two writers landing on the same hook or the same headline is a wasted ad, and it happens because they worked blind to each other. Send the weaker one back with the collision named and ask for a replacement variation.
2. **Consistency check.** Every variation still sits on the awareness level the brief assigned it. A writer that drifted to a different level gets that variation rewritten.
3. **Style collision.** No more than two assets across the batch share the same palette and layout. Send the later one back with the collision named.
4. **Append to the tracker.** The batch goes into the creative memory tracker, one profile per ad, `status` set to `new`, using the shape in `creative-memory-tracker.md`. At the same time, collect every writer's prompts into the single prompts file described in `generator-handoff.md`, numbered and grouped by concept.

## If you cannot spawn writers

Some runtimes cannot start helper agents. When yours cannot, write the concepts one at a time, in the same order, with the same inputs listed above, then run the same four steps.

Decide this yourself from what your runtime can do. Never ask the owner to pick. Just tell them in one line which way you did it.
