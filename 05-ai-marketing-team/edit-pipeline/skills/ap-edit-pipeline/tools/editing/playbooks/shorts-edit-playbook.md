# Short-form edit playbook

One raw talking-to-camera clip becomes a vertical short with clean captions,
b-roll that is actually motivated, and, if the member wants to spend on it, a
couple of short generated effect beats.

This is a rebuild of a published creator workflow, in our own words, with the
tool-specific parts replaced by the principle underneath, so it works with
whatever the member already owns. The chain in the folder above does the cutting.

## The two rules that make it look human-made

1. **Stay real for all talking.** Effects go on specific beats only. Long
   generated renders of a face drift and look fake. Short motivated beats look
   like magic.
2. **Polish beats clutter.** A good caption font and one cutaway that makes
   sense beats a pile of glowing overlays. Restraint is the whole trick.

## Order of operations

1. **Transcribe with word timings.** Prime the vocabulary first: pass the topic
   and the proper nouns to `transcribe.py --initial-prompt`. Their product name,
   their industry words, the client type they say fifty times. Fewer mishears up
   front is cheaper than fixing captions later.
2. **Correct the transcript before anything reads it.** Every word is going on
   screen as a caption, so a mishear is a typo in high definition, and accents
   and industry words are exactly what the engines get wrong. Rules for this
   pass:
   - Correct words **in place**. Timings are untouchable.
   - If a fix splits or merges words, map the corrected words onto the original
     word's time span.
   - Faithful, not pretty. Fix mishears only, never rephrase, because rephrasing
     desyncs the words from the audio.
   - Captions, cutaway triggers and every later step read only the corrected
     file.
   - Each new mishear becomes a standing line in the member's rules file
     (`content-os/MY-RULES.md` when Content OS is set up, otherwise
     `MY-EDIT-RULES.md` at the top of the media workspace), under a heading for
     words the transcriber gets wrong, so the same name is never wrong twice.
3. **Clean the take.** Marker cuts first (`cutcut.py`). Then, only if the member
   wants it tighter, repeats, false starts, and pauses over about 0.3 seconds.
   **Show the cut list before cutting.**
4. **Even out the audio.** `render_cuts.py --normalize-audio` does a gentle
   de-noise and levels to -14 LUFS, which is what short-form platforms expect.
   Clean, even audio is half of what people mean by professional.
5. **Effect beats, only if the member wants to spend.** See the rules below.
6. **Polish.** Word-by-word captions, one lower third at most, a cutaway on a
   concrete noun, a warm grade, a soft vignette.
7. **Assemble vertical, final audio pass, render, watch it.**

## Captions that read as premium, not cheap

- **A real display font.** A heavy caption face beats the default system font,
  and it is the single biggest cheap-versus-premium tell. Anton is a common free
  one. Whatever the member's brand font is, use that.
- **Their accent colour on the spoken word**, everything else dimmed. The
  overlay layer in this pack does exactly that, and the colour comes from the
  brand colour recorded in their rules file.
- **Four words on screen at a time**, not a wall of text.
- **Keep captions out of the bottom safe area** where the platform puts its own
  interface.

## Cutaways

- **Word-locked.** Cut away on a concrete visual noun the member actually said.
  One cutaway that matches the word beats ten that do not.
- **Short.** About 1.5 to 2.5 seconds, then back to the face.
- **Check the context.** "Cuts" in an edit is not "cuts" in a butcher shop. Read
  the sentence, not the word.
- **Never decorative.** If it does not prove, clarify, orient or reset
  attention, it is clutter.

## Generated effect beats: the rules that keep them looking like the member

This lane costs money. It needs a paid generation service and it is entirely
optional. The whole rest of this playbook is free. When the member does want it,
these are the rules that separate a beat that looks like magic from one that
looks like a deepfake of their own face.

- **Lock, then change one thing.** State everything that is preserved: face,
  wardrobe, performance, framing, camera. Name the single change. Repeat that
  face and identity are unchanged at the end of the instruction.
- **Match the source length.** One to two seconds reads as magic. Six to nine
  seconds drifts.
- **Lock the framing.** These tools love to zoom and recompose. Say not to.
- **Real face for spoken lines.** Generated mouths break lip sync. Use effect
  beats on non-talking moments only.
- **Audio off on every generated clip, the member's real audio back over it.**
  Never keep a generated voice.
- **The change lands on or after a snap or a gesture**, never before. Find the
  frame and cut there.
- **Generic creatures and objects only.** Never anything branded or
  recognisable from someone else's property.
- **Warm daylight scenes are safest.** Night and neon relight the face and raise
  the risk of drift.
- **Light integration beats colour matching.** Key direction, softness, spill,
  a little haze. No cut-out edges.
- **Still first, then animate.** Generate the transformed opening frame as an
  image, lock the look, and only then spend on video.
- **If an intro is prepended to a fixed total length**, subtract it. Total minus
  intro is what is left for the real take. If the take is longer, either extend
  the total, start the take earlier, or accept the truncation, and say which.

## Checkpoints the member approves

- [ ] The cut list, before anything is cut.
- [ ] The list of effect beats and cutaway moments, before a single paid credit
      is spent.
- [ ] The master, watched all the way through, before any export.

First few pieces: nail the captions and one good cutaway before touching
effects. Add one beat, not ten.

## What it costs

The whole chain in this pack is free: the cutting engine, the transcription
engine, the caption and overlay layer. The only paid part is a generation
service for effect beats, and that is optional. Captions and cutaways alone
cost nothing beyond what the member already pays for their agent.
