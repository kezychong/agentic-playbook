# Generator handoff

This file is for the agent. Load it only after the owner has approved the brief.

## The gate

If the owner has not said yes to the brief, stop reading and go back. Nothing in this file happens before approval. Not a test image, not one prompt, nothing.

## One prompt per creative

The prompts themselves now come back from the writers, one writer per concept, as set out in `sub-writers.md`. This file stays the rulebook those prompts have to obey, and it is what you check them against before anything gets generated.

N approved creatives means N prompts. Write them all into one file in the owner's folder, for example `ad-review/prompts-YYYY-MM-DD.md`, numbered and grouped by concept, so they can be pasted one after another without hunting.

Each prompt is complete on its own. A generator has no memory of the brief.

### Video prompt shape

Write it as plain description, in this order:

1. **Who is in it and where.** The person, the setting, the mood, the time of day.
2. **What happens.** The action, in order, beat by beat.
3. **How it is shot.** Framing and camera movement. Handheld selfie, static talking head, slow push in, over the shoulder.
4. **On-screen text.** Only where captions sit. The exact words never go to the generator: burned-in lines, prices and end cards are laid on last (see Words go on last).
5. **The spoken line.** Word for word, the same line that is in the brief.
6. **Length in seconds.** Always. Say it in the prompt.
7. **No music.** Always say "no music" unless music is actually wanted for this ad. Generators add a soundtrack by default, and a soundtrack ruins a voice ad and makes the audio useless for anything else later.
8. **Aspect ratio.** Nine by sixteen for feed and stories unless the brief says otherwise.

### Image prompt shape

The picture only. The prompt describes subject, composition, style, colour and the aspect ratio (4:5 unless the brief says otherwise) and ends with: no text, no captions, no logos, no watermarks. The generator never spells the headline.

## Words go on last

Write a small HTML file at the final size: 1080 by 1350 for 4:5, or 1080 by 1920 for 9:16. Use the generated picture as the background. Place the headline, price and date as real text. Use the browser already on the Mac to screenshot it:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --window-size=1080,1350 --screenshot=out.png "file:///path/card.html"
```

Set the HTML canvas and browser window to 1080 by 1920 for 9:16. If Chrome is absent, use a Python image library. Open the PNG and read every word back against the brief. Keep these commands agent-facing; the owner never runs them.

Video end cards get the same treatment at 1080 by 1920 and are joined to the clip with ffmpeg.

## Before the first video

Before the first video, decide two things once. Ask the owner whether the videos use their own voice (one clean video with no music as the reference) or a narrator. Check the generator's remaining credits against the batch size; if credits are short, generate the images first and say so.

## Using their own voice

If the account already has a video ad with a clean voice and no music, that file is a voice reference. You downloaded it in step 3, so it is already sitting in the assets folder.

Upload that one video to the generator and tell it to use this voice as the reference for the new videos. The new ads then sound like the owner instead of like a stock narrator.

Two things worth telling the owner in one line each:

- **This is why "no music" matters.** A clean voice track can be reused. A voice buried under a soundtrack cannot.
- **More audio makes a better clone.** One clip gets a decent match. If they want the voice to be genuinely theirs across everything, a professional voice cloning tool trained on more of their recordings is the upgrade, and the cloned voice can then be fed into the video tool.

## When the tool only has a website

Some of the best generators have no proper connection for an agent. Higgsfield is one of them, and its unlimited mode is where a big batch gets cheap.

That is not a blocker. Take over the browser and use the site the way a person would:

1. Ask the owner to open the tool and sign in themselves. You never type or ask for their sign-in details.
2. Go to the generator, pick the model and the mode they want.
3. Enter the prompts one by one, from the prompt file, in order.
4. Keep a simple list of which prompt produced which output, so the review pass is not guesswork.

Sizes: 4:5 for feed images, 9:16 for video and stories. Never 1:1 unless the owner asks.

Useful limits to design around: Seedance produces up to about thirty seconds, and unlimited mode usually caps around twenty. Both are fine ad lengths. Write for the limit instead of fighting it.

## The volume mindset

Launch many. Let the platform sort out which one works.

That is the reason for the batch. With AI doing the generation, the smart move is coverage, not perfection. A detail you would have agonised over is almost always covered by another ad in the batch.

Say this to the owner if they start polishing prompt number three for the fourth time.

## The quality gate

Check every asset before showing the batch:

- [ ] No placeholder text, brackets or curly braces.
- [ ] Every word matches the brief letter for letter.
- [ ] The right size: 4:5 for feed images, 9:16 for video and stories.
- [ ] No gibberish anywhere.
- [ ] No two-alike looks: no more than two assets share the same palette and layout.
- [ ] The account's own proven format is present.
- [ ] The business is on screen by second five of any video, unless the owner approved a story hook.

## The batch contact sheet

Build one image of every asset in the batch, using ffmpeg tile or a Python image library. Use a representative frame for each video and label every asset by concept and variation. Show it to the owner for keep or kill before any upscale, crop or re-voice.

## The review pass

When the batch is generated, show them the outputs grouped by concept.

- They keep the ones that work.
- You re-prompt the weak ones. Change the one thing that broke it, not the whole prompt.
- Download the keepers into a clean folder in their own project, named so a human can tell them apart, for example `concept-2-var-4-hook-question.mp4`.

Then update each creative's existing entry in the creative memory tracker (the sub-writers pass already appended the batch as `new`): mark which ones were kept, note which were re-prompted, and add a one line note saying what the variation was testing. Do not append them a second time.

## Where this stops

This skill produces files. It does not upload the creatives into the ad account, build the campaigns, or set budgets. That is the media buying job and it is a different piece of work.

Finish by telling the owner plainly: the creatives are in this folder, the tracker is updated, and the next run will read all of it.
