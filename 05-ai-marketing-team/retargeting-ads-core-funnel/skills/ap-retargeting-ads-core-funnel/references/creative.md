# Creative Generation — 25 Ads Per Layer

For each layer you build, you generate **5 concepts × 5 variations = 25 image ads.** Across all three layers that totals 15 ad concepts and 75 ad variations — you are NOT generating 75 concepts; concepts are 5 per layer, variations are 5 per concept. You (Claude) write these — pull the customer from `audience.md`, the offer from `offer.md`, and match the message to the layer's awareness level.

## Why image ads first

Default to image ads. They are much faster to create and iterate than video — you can produce and test 25 in the time one good video takes. Video is allowed and variety helps, but images are the workhorse of this system. For layer 1, reusing image ads that already ran is fine; adding new concepts on top is encouraged.

## What "5 concepts × 5 variations" means

- A **concept** is a distinct angle — a different big idea, hook, or emotional entry point.
- A **variation** is the same concept expressed 5 different ways — different headline wording, different opening line, different framing of the same idea.
- So each layer gives you 5 genuinely different angles, each stress-tested 5 ways = 25 ads to test.

## The generation flow

When the user asks you to generate creative for a layer:

1. **Read `audience.md` and `offer.md`.** If either is missing, build it first (see `context-files.md`). Never generate ads on generic assumptions.
2. **Identify the layer and its awareness level** (problem / solution / product).
3. **Generate 5 concepts** appropriate to that awareness level, each grounded in the real customer and offer.
4. **For each concept, write 5 variations** — vary the headline and hook, keep the concept intact.
5. **For image ads, describe the visual** alongside the copy — what's on the image, the headline text overlay, and the primary text that runs with the ad.
6. Deliver all 25 in one organized file the user can hand to a designer or an image generator.

## The three prompt shapes

These are the shapes to follow for each layer. Adapt the wording to the user's real audience and offer — keep the structure.

**Layer 1 — Problem-based (video viewers who didn't opt in):**
> "I want to retarget people who watched my video but did not come to my landing page. [State the offer.] They are semi-cold and problem-aware. Create a problem-based retargeting ad — give me 5 concepts and 5 variations each."

**Layer 2 — Solution-based (opt-in visitors who didn't book):**
> "I want to create a retargeting campaign for `audience.md`; my offer is `offer.md`. Because they came to the landing page but did not book, they really understand the problem. Create a solution-awareness retargeting ad — 5 concepts and 5 variations each."

**Layer 3 — Product/offer-based (booking page visitors who didn't book):**
> "I want to create a retargeting campaign for people who came to my booking page but did not book. These are people who are solution-aware, so create product-aware retargeting ads. For `audience.md`; my offer is `offer.md`. Create 5 concepts and 5 variations each."

## Matching message to awareness — the rule

- **Problem-based (layer 1):** lead with the pain. Make them feel seen. The goal is the click to the landing page. Don't over-pitch a cold viewer.
- **Solution-based (layer 2):** they already feel the problem. Show your approach is the way out. Contrast the old broken way with your way.
- **Product/offer-based (layer 3):** they know the solution. Now sell the specific offer — the promise, the reason to act now, and answers to the hesitation that stopped them at the calendar.

## Quality checks on generated creative

- Every ad names something real from `audience.md` and `offer.md` — no generic "transform your life" filler.
- The angle matches the layer's awareness level (don't hard-pitch the offer to a cold layer-1 viewer).
- Headlines are specific. A specific number, situation, or phrase from the customer's own language beats a vague promise.
- Concepts are genuinely different from each other, not five rewordings of one idea.
