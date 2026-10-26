
# First time only: setting up the two free tools

Read this once, on the first edit on a machine, and never again after that.

**Triggers:** "set up my editor", "set up the editing tools", or the first ever edit
request on this machine.

## Check before you ask

Run `tools/editing/setup_editing.py --check`. It reports what this machine already
has, in plain sentences and in a machine-readable form, and it installs nothing.

If `core_chain_ready` comes back true, say nothing about setup at all. Just edit. A
member who is ready does not need to hear about tools.

## The words, when something is missing

Say this, in these words, and wait:

```text
Before your first edit I need to set up two free tools on this computer. One
cuts and re-renders video. One turns your speech into words with the exact
moment you said each one, which is how the cut lands on the right syllable
instead of near it.

Both run on your machine. Nothing is uploaded anywhere, and neither one costs
anything. The download is around 3GB the first time and then it is done
forever. Shall I go ahead?
```

Wait for a yes. Then install, narrate once at the start and once at the end, and say
when it is done in one sentence. No progress spam.

```text
Agent procedure: first-time setup

1. Run tools/editing/setup_editing.py --check and read the report.
2. If core_chain_ready is true, say nothing about setup. Just edit.
3. If it is false, say the paragraph above, in plain words, and WAIT.
4. On a yes: setup_editing.py --install engine, then --install ffmpeg.
   Narrate once at the start, once at the end.
5. If package_manager is null, do not pretend. Say this machine cannot install
   them, and offer the by-hand road in 01-the-run.md.
6. Never install the caption and overlay tool at this point. That one waits for
   the first time captions are actually asked for. See 03-captions.md.
```

## Honest notes, given before we start and not after

- On a recent Mac this is quick. A few minutes for a normal recording.
- On a Windows machine or an older Mac, the engine that works there is slower. A ten
  minute recording can take a while. Say so before starting, and offer a smaller,
  faster model if they would rather have speed than the last few percent of accuracy.
- If this machine has no way to install anything, say that plainly and take the
  by-hand road. Nothing about this is a dead end.

## Where the tools get installed

Into a private tools folder inside the media workspace, not into the machine's shared
setup. The member's existing machine is left exactly as it was.

The video tool and the caption tool install through the machine's own package manager.
When there is no package manager, the check says so instead of pretending.

## What runs where

| Engine | Where it works | Notes |
|---|---|---|
| mlx-whisper | Apple Silicon Macs | Fast. Best first choice. Model download about 3GB, once. |
| openai-whisper | Anywhere | Slower without a graphics chip. A ten minute recording takes a while. Offer a smaller model. |
| whisper.cpp | Anywhere, if already installed | Fast on a plain processor. Needs a model file. Word timings are grouped from its token output, so check the first result. |

`tools/editing/transcribe.py` picks the best available and writes the same shape
whichever one runs, so nothing after it cares which engine was used.

## Next

Setup done, go straight back to `01-the-run.md` and do the edit they actually asked
for. Do not make setup the conversation.
