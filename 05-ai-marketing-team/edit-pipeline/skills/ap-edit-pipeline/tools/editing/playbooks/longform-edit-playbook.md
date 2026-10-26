# Long-form edit playbook

One long take, a webinar promo, a lesson, a talking-head video, becomes an edit
that looks like a team packaged it. The idea in one line: **clean the take, then
design on top of it.** Every graphic has to be earned by the words.

This is a rebuild of a published creator workflow, in our own words, with the
tool-specific parts replaced by the principle underneath, so it works with
whatever design tool the member has. The chain in the folder above does the
cutting.

## The eight steps

1. **Check the format and keep it.** Read the recording's real size and frame
   rate first, and stay native the whole way. If it was filmed in 4K it stays 4K.

2. **Transcribe with word-level timing.** Everything else snaps to those words.
   Prime the vocabulary with the topic and the proper nouns
   (`transcribe.py --initial-prompt`).

3. **Correct the transcript before anything reads it.** The engines mishear
   accents, names and industry words, and raw output is not caption-ready.
   - Correct words **in place**. Timings are untouchable.
   - If a fix splits or merges words, map the corrected words onto the original
     word's time span.
   - Fix mishears only. Never rephrase, because rephrasing desyncs the words
     from the audio.
   - Captions, cutaway triggers and graphics all read the corrected file only.
   - Each new mishear becomes a standing line in the member's rules file
     (`content-os/MY-RULES.md` when Content OS is set up, otherwise
     `MY-EDIT-RULES.md` at the top of the media workspace), so the same word is
     never wrong twice.

4. **Clean the take.** Marker cuts are the primary method (`cutcut.py`). For
   stretches with no marker, these two tricks find what the transcript hides:
   - **Filler words in voiced gaps.** A pause with sound in it is usually an
     "um". Clip that gap out, transcribe just that clip, and see.
   - **Filler words inside stretched words.** A normal word that lasts about 1.5
     seconds is usually "[um] word". Find the quiet part inside it and cut just
     that.
   - Then tighten pauses over about 0.3 seconds, and cut stumbles, false starts
     and repeats.
   - **Every cut shifts everything after it.** Recompute the timings, or
     transcribe the trimmed version again, before anything else reads them.

5. **Even out the audio.** Gentle de-noise, then level to -14 LUFS
   (`render_cuts.py --normalize-audio`). Clean audio is half of what people mean
   when they say a video looks professional.

6. **Design the graphics, in the order they appear.**
   - **Intro moment.** Something small and moving, so the open is not just a
     face.
   - **Claim cards.** A full-frame card for a big statement. Add a simple chart
     when the point is about scale or results.
   - **Picture-in-picture with a step list.** The face shrinks into a rounded
     corner while a numbered list builds beside it, each step lighting up as it
     is spoken. This is the single most designed-looking move available, and it
     costs nothing but layout.
   - **Show what the words say.** If the words describe a process, show the
     process. Match the visual to the word.
   - **Captions as emphasis, not wallpaper.** Centre-bottom on a full frame,
     anchored to the video panel on a split layout.
   - **A payoff card at the end**, over relevant footage, with a readable dark
     panel behind the text.
   - **Finish with a subtle vignette and a little grain** to unify everything.
   - The rule over all of it: **every graphic is earned by the words.** If it
     does not illustrate or emphasise what is being said, cut it.

7. **Cutaways, only where they make sense.**
   - **Word-locked** to concrete visual nouns actually spoken. About 1.5 to 2.5
     seconds, then back to the face.
   - **Check the context** before matching a word to a picture.
   - **Generate the still first, then animate it**, when using a generation
     service. It gives far more control over look and brand than going straight
     to video.
   - **Match the grade** of every cutaway to the main footage.
   - **Composite cutaways underneath the graphics**, inside the design, not
     pasted on top of a finished render.
   - Keep the ones that work in a folder in the media workspace and reuse them.

8. **Render two versions, with and without the cutaways.** Watching them back to
   back is the honest test of whether the extra footage earned its place. Often
   it did not.

## Checkpoints the member approves

- [ ] The cut list, before anything is cut.
- [ ] The cutaway moments, before any paid generation.
- [ ] The master, watched all the way through, before any export.

Everything up to the graphics render is free, so iterate there.

## Brand consistency

Pick the colours and the font once, from the member's own brand, and commit to
them across every video. Consistency beats flourish. A member with no brand kit
gets one accent colour and one heavy display font, and that is enough.

## Hard-won lessons worth keeping

- Transcripts drop filler words. Hunt them in voiced gaps and inside abnormally
  long words.
- Cutting shifts every timing after it. Recompute or re-transcribe.
- Cutaways are word-motivated, short and context-checked. Never decorative.
- Generating a still and animating it beats generating video from a description.
- Composite the extra footage inside the design so graphics render on top.
- Clean audio, a consistent grade and earned graphics are what "a team made
  this" actually means.

## What it costs

The cutting, the transcription, the captions and the overlays cost nothing
beyond what the member already pays for their agent. A generation service for
cutaway footage is the only paid part, and no cutaways means no cost.
