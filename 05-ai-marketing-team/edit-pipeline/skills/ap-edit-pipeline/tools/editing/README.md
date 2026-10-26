# tools/editing/ - the edit chain

Agent-facing notes. The member never opens this folder and never needs to know
any of it. The member-facing run file is `references/01-the-run.md`; read that
for what to say and when to stop. This file is what the parts do.

One recording in, one clean master out, then the three delivery sizes. The
member's editing hours are replaced by one watch-through, not by their judgment.

## The parts

| File | Job | In, out |
|---|---|---|
| `setup_editing.py` | Find or install the free tools. Reports in plain sentences and in JSON. | machine, report |
| `media_workspace.py` | Decide where media is allowed to live and refuse the rest. | path, verdict |
| `transcribe.py` | Recording to words with exact timings. Three engines, one output shape. | video, `*.words.json` |
| `cutcut.py` | Marker word to cut list, keeping the last take. Pure logic, no video touched. | words, `*.cuts.json` |
| `silence_trim.py` | OPTIONAL dead-air removal. Off by default. | master, `*.cuts.json` |
| `render_cuts.py` | Run a cut list, write the clean master. Optional audio levelling. | cuts and video, `master.mp4` |
| `export_presets.py` | The approved master out at 9:16, 1:1 and 16:9. | master, three files |
| `overlay/` | OPTIONAL captions, proof images and hook line. See `overlay/README.md`. | master, captioned master |
| `playbooks/` | Two rebuilt craft playbooks: short-form and long-form. | reading |
| `tests/` | The test suite. `python3 tests/run_all.py`. | verdict |

Every part does one job, has a real `--help`, and can be run on its own.

## The normal run

```
0. setup_editing.py --check                       first time only, and after any failure
1. transcribe.py raw.mp4 -o take.words.json       add --initial-prompt with their words
2. cutcut.py take.words.json -o take.cuts.json --marker "cut cut"
   -> SHOW THE MEMBER the plain summary. This gate is not optional.
3. render_cuts.py take.cuts.json raw.mp4 -o master.mp4
   -> THE MEMBER WATCHES IT. Their job, every time.
4. export_presets.py master.mp4 --out-dir exports  only after they approve
```

Optional rungs, only when asked, only on an approved master:

```
silence_trim.py master.mp4 -o silence.cuts.json   then render_cuts.py again
overlay/bootstrap_overlay.py                      once, the first time captions are asked for
overlay/render_overlays.py ... then overlay/composite.py
```

## How far back a marker deletes: pick the scope, do not guess

`cutcut.py --scope` has two settings, because two filming styles exist and the
wrong one is destructive.

- **`full-take`, the default.** A marker deletes everything back to the previous
  marker or to the start. This is how the tested original works, and it is right
  when the recording is a run of separate attempts at the same short line.
- **`line`.** A marker deletes back only to the fumbled line: the latest
  sentence ending or real pause before it. This is right when somebody filmed
  one continuous take from bullet points and fumbled once in the middle, which
  is what most talking-to-camera filming guides tell people to do. Under
  `full-take` that member loses every good minute before the fumble.

How to choose without asking a technical question: run the default, read the cut
list, and look at what it removes. `cutcut.py` warns by itself when a removed
piece runs longer than 15 seconds, because a single fumbled line is not 15
seconds. On that warning, run it again with `--scope line`, show both, and
recommend one with the reason in one sentence.

Two robustness notes worth knowing:

- The marker is matched both as two words ("cut cut") and as one joined word,
  because said quickly the engines return "CutCut" or "cut-cut". A missed marker
  leaves the fumble in the video.
- `line` scope produces MORE than one surviving stretch, which is the case the
  render has to join correctly. That is covered by a test.

## The gates, in order of how badly it goes when they are skipped

1. **Show the cut list before cutting.** `cutcut.py` prints a plain summary:
   how many markers, what is being removed, what each removed piece said. That
   is the evidence trail. Read it out. Do not paraphrase it into "I cleaned it up".
2. **The member watches the master before any export.** Every time. This is the
   one job the chain does not take from them.
3. **The overlay layer gets its own watch-through.** Captions land on the wrong
   word sometimes and an image can cover a face.
4. **Nothing is posted, ever, by anything in here.** The chain writes files. The
   member publishes.

## Stop and ask when

- The transcript looks garbled: repeated words, stuck timings, nonsense strings.
  Do not build a cut list on a bad transcript.
- The number of markers does not match what the member remembers doing.
- More than one stretch survives on the default scope, where only the last take
  should ever survive.
- A surviving stretch is suspiciously short.
- Anything would need a tool outside ffmpeg, a transcription engine, and node
  for the optional layer.

Never render a guess. An honest question costs a minute; a wrong cut costs the
whole take.

## Where files live, and why it is a rule

- Media, renders and the installed tools live in the **media workspace**,
  `~/ContentStudio` by default, or wherever `CONTENT_OS_MEDIA_DIR` points.
- **Never** inside `content-os/`. That workspace holds text: cards, scripts,
  rules. `media_workspace.py` refuses.
- **Never** inside a cloud-synced folder: iCloud, Dropbox, OneDrive, Google
  Drive, Box and the rest. Sync services choke on video and eat storage plans.
  `media_workspace.py` refuses to write there and warns when a source file is
  there.
- What goes back into `content-os/` is text only: an `## Edit record, YYYY-MM-DD`
  section appended to that idea's script file, saying what was cut, how long the
  master runs, where the files are, and what the member said at the
  watch-through.

## Engines and honest platform notes

| Engine | Where it works | Notes |
|---|---|---|
| mlx-whisper | Apple Silicon Macs | Fast. Best first choice. Model download about 3GB, once. |
| openai-whisper | Anywhere | Slower without a graphics chip. A ten minute recording takes a while. Offer a smaller model. |
| whisper.cpp | Anywhere, if already installed | Fast on a plain processor. Needs a model file. Word timings are grouped from its token output, so check the first result. |

`transcribe.py` picks the best available and writes the same shape whichever
runs, so nothing downstream cares. ffmpeg is needed either way, because every
engine decodes video through it.

`setup_editing.py --install engine` builds a private tools folder inside the
media workspace and installs there, so the machine's shared setup is never
touched. ffmpeg and node install through the machine's own package manager
(Homebrew on macOS, winget on Windows, apt or dnf or pacman on Linux). When
there is no package manager it says so plainly instead of pretending.

## Honest maturity

These are preserved source tools and test fixtures. The source described earlier synthetic checks, but none of those checks or real-footage runs were reproduced for this repackage. Treat the full chain, overlays and platform support as untested here. Review every cut list and watch every master before exporting or publishing.

## Tests

```
python3 tests/run_all.py
```

- `tests/test_cutcut.py` pins the exact keep and removed windows. Must pass. No
  tools needed.
- `tests/test_props_builder.py` pins the overlay props contract. Must pass. No
  tools needed.
- `tests/test_chain.py` pins the media rules, the silence maths, the render and
  export planning, and the transcript normalising. Parts skip without ffmpeg.
- `tests/test_e2e_synthetic.py` makes its own recording and drives the real
  tools. Skips cleanly when the machine cannot run it.

## Credit

The marker method ("say a word when you fumble, keep rolling, delete backwards
in the edit") is a proven creator filming protocol, widely taught in short-form
filming guides. The pack rebuilt it in its own words and its own code. The two
craft playbooks in `playbooks/` are rebuilds of published creator workflows,
credited generically, with the tool-specific parts replaced by principles the
member can use with whatever they own.
