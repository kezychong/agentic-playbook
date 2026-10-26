# overlay/ - captions, proof images and the hook line

Agent-facing notes for the optional layer. The member never reads this file, and
never has to know any of it. The whole edit chain works without this folder.

## What it does

Adds styled layers on top of the approved master:

- word-by-word captions, driven by the same words JSON the cut used,
- proof images anchored to the moment the words claim something,
- a big opening line on the first couple of seconds.

## The architecture, which does not change

The app renders a **see-through** video that contains only the layers. It never
contains the master. ffmpeg then stacks that over the master.

**The app draws layers. ffmpeg does the stacking.** Keep it that way: it is why
the audio is never touched, why the master is never re-encoded twice, and why a
bad overlay is thrown away without hurting the approved master.

## The pieces

| File | Job |
|---|---|
| `bootstrap_overlay.py` | Copy the app into the media workspace and install its parts there. Never inside the pack. |
| `render_overlays.py` | Words plus manifest, out comes a see-through `overlay.mov`. |
| `composite.py` | Stack the overlay over the master. Audio copied straight through. |
| `props_builder.py` | Pure transform: words plus manifest, out comes the props object. No extra tooling, with supplied unit-test source; those tests were not run here. |
| `src/` | The layer components: `Captions.tsx`, `ProofOverlay.tsx`, `HookText.tsx`, wired in `Overlay.tsx` and `Root.tsx`. |
| `example-manifest.json` | Every field, with an example value. |

## Order of operations

```
1. bootstrap_overlay.py                  once, or after the source changes
2. stage proof images into <media workspace>/overlay-app/public/   by file name
3. render_overlays.py --words ... --manifest ... --master ... -o overlay.mov
4. composite.py --master ... --overlay overlay.mov -o master-captioned.mp4
5. the member watches it, again
```

## Gate

**Never run this on a master the member has not approved.** The overlay layer
presupposes a finished, watched, approved master. Its own output then gets its
own watch-through, because captions land on the wrong word sometimes, an image
can cover a face, and a hook can mistime.

## Manifest fields

Times are in seconds and match the words JSON.

- `hook_text` (string): the opening line. An empty string turns the layer off.
- `hook_duration_seconds` (number, default 2.0).
- `captions.enabled` (bool, default true). False drops every caption word.
- `captions.font_size_px` (default 72), `active_color` (default `#FFFFFF`),
  `inactive_color` (default `#B8B8B8`), `bottom_margin_px` (default 320),
  `max_words_per_group` (default 4).
- `proof_assets[]`: `path` (must be in the media workspace), `start`, `end`,
  `position` (`top` / `center` / `bottom`), `caption` (empty string means none).

Any field left out falls back to the default in `src/Root.tsx`, which
`props_builder.py` mirrors exactly. A manifest of `{"captions": {"enabled": true}}`
renders identically on both sides.

Set `active_color` from the member's own brand colour, recorded in their rules
file, rather than leaving the neutral default, if they gave one.

## Where things live

- The pack holds the app **source**: the `.tsx`, `.ts`, `.json` and `.py` files.
- The installed parts, the renders and the proof images live in the media
  workspace (`~/ContentStudio` by default). Never in the pack, never in
  `content-os/`, never in a cloud-synced folder. `media_workspace.py` refuses.

## Honest state

The source reports that an earlier version passed a synthetic render
test and had zero runs on real footage. Treat the first few outputs as drafts
and watch them properly. Nothing about it is proven on a real business video
yet, and the pack says so rather than pretending otherwise.

## Notes worth keeping

- The four flags that make the output see-through are
  `--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png`.
- Props are passed as a file path, not as a blob on the command line.
- Proof images resolve by file name from the app's `public/` folder, so they get
  staged there before the render.
- The version numbers in `package.json` are pinned on purpose. Check a version
  exists before changing a pin.
