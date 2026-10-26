
# Captions and on-screen proof

Optional. Only ever on a master the member has already watched and approved.

**Triggers:** "add captions", "make my captions", "put captions on this", "put my
hook on screen", "show the number on screen".

## The one gate that comes before everything else

If the master has not been approved, stop. Go back to `01-the-run.md`, finish the
edit, get the watch-through, and come back. Captions on an unapproved master waste
the render and confuse the member about what they are looking at.

## The first time only

One more free tool is needed. Say this, once, and wait:

> Captions burned into the video need one more free tool. Two minutes to set up,
> once. Want me to?

On a yes, install it and say when it is done, in one sentence. If the machine cannot
install it, say so plainly and offer the alternative: the platforms themselves add
automatic captions on upload, and their transcript is already sitting in the run
folder if they want to paste corrected words in.

## What the captions are built from

Three inputs, and each one has an answer whether or not they run Content OS.

- **The hook line.** The big opening line on the first couple of seconds. If they
  run Content OS, it is the on-screen hook already written in their recording pack.
  If not, ask for it in one sentence, or leave it out. An empty hook simply turns
  that layer off.
- **The proof images.** Anything they want on screen at the moment the words claim
  the thing. If they run Content OS these come from the same recording pack. If not,
  ask what they have and where it is. None is a perfectly good answer.
- **The colour and the font.** From whatever they told you about their brand,
  recorded in their rules file. If they never gave one, captions are white on the
  spoken word and dimmed grey on the rest, which reads cleanly over anything.

Never ask for all three at once. Ask for what is missing, in one short question.

```text
Agent procedure: captions and overlays

1. Only after the master is approved. Never on an unapproved master.
2. setup_editing.py --install overlay, once, after asking.
3. tools/editing/overlay/bootstrap_overlay.py, once.
4. Copy the manifest shape from tools/editing/overlay/example-manifest.json into
   the run folder and fill it from the three inputs above. Every field left out
   falls back to a sane default; a manifest with nothing but captions enabled
   renders correctly.
5. Stage any proof images into the app's public folder inside the media
   workspace, by file name.
6. overlay/render_overlays.py --words ... --manifest ... --master ... -o overlay.mov
7. overlay/composite.py --master ... --overlay ... -o master-captioned.mp4
8. THEY WATCH IT AGAIN. Captions land on the wrong word sometimes and an image
   can cover a face. Second watch, every time.
```

## How it is built, and why that matters

The app draws a see-through video containing only the layers. It never contains the
master. The video tool then stacks that on top. That is why the audio is never
touched, why the master is never re-encoded twice, and why a bad overlay can be
thrown away without hurting the approved master.

Keep it that way. Full agent notes: `tools/editing/overlay/README.md`.

## The second watch-through

Non-negotiable, same as the first. Captions land on the wrong word sometimes. An
image can cover a face. A hook can mistime by half a second and look sloppy.

If they flag a misheard word, fix it and then ask the standing question: should I
remember that as a rule? On a yes it goes into their rules file under the words the
transcriber gets wrong, so the same name is never wrong twice.

## Honest state

The supplied source reports earlier synthetic and limited render tests; those results were not reproduced in this repackage. Treat
the first few outputs on their footage as drafts and watch them properly. Nothing
about it is proven across hundreds of real business videos, and this pack does not
say otherwise.
