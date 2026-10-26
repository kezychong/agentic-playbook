# Host compatibility and safe staging

**Optional extra, Mac main device only.** These patches are not required for JARVIS Mode to work, and the core install never waits on them.
**The version 1.0.0 voice door is the stock Hermes Desktop call**, the round voice button beside the message box, or the Talk plugin when the member already runs it.

This component packages the six-commit Hermes desktop voice chain and the
optional Talk presence bus. It is a staged-tree payload. The helper never edits
a running app, an installed plugin directory, or a live checkout.

The host voice sequence is ordered from the public Hermes base recorded in
voice-patch-compatibility.json:

1. voice-1 exposes guarded composer voice ownership.
2. voice-2 completes the scoped Talk voice host contract.
3. voice-3 keeps Talk failures visible and resets owner lifetime.
4. voice-4 binds Talk dashboard tasks to the verified caller and canonical
   requested profile.
5. voice-5 keeps a call through a link blink and changes the identity rule for
   a stored chat.
6. voice-6 extends the same grace gate to GPT-Live delegation submits and
   keeps the submit-time session identity.

The patches preserve the native voice controller. The JARVIS desktop controller
is supplied by the main frontend component and remains the owner of the native
SDK route.

Compatibility is exact-source based. The helper requires a marked, clean Git
staging tree and the base SHA-256 values for all 16 chain files in
voice-patch-compatibility.json. It verifies the post-patch hashes after each
step. A different source tree, an omitted carried capability, or an unexpected
local edit is reported as unsupported. The package makes no Hermes version
promise and never silently drops a patch behavior. The unrelated subscription
and billing carry is intentionally excluded.

The public source route is https://github.com/NousResearch/hermes-agent. The
official v0.21.3 release tag v2026.9.14 (345cd2b) is an ancestor of the exact
public base e83b1d51f13 used here. An installed app alone does not satisfy the
hash gate; obtain a source checkout, pin it to e83b1d51f13, and apply voice-1
through voice-6 in order. Any other latest source requires exact hash matching
or a deliberate compatibility adaptation.

## Agent-led public checkout and build route

The agent obtains the public source into a new recovery directory. It does not
reuse or edit a member's live checkout:

    git clone https://github.com/NousResearch/hermes-agent.git /recovery/hermes-source
    git -C /recovery/hermes-source checkout --detach e83b1d51f13a08b424636f0b519db86a35aa7bd7
    git -C /recovery/hermes-source rev-parse HEAD

The last command must print the exact base commit. The agent then adds
.jarvis-staged-tree.json containing {"kind":"jarvis-host-staging"}, commits
that marker, and confirms a clean tree. The base has 11 of the 16 chain files;
the remaining five are created by the first two voice patches. No other files
are copied into the tree.

The desktop workspace is a root npm workspace. Check the engines declared by
the pinned checkout before installing: Node must satisfy
`^22.22.0 || ^24.11.0 || >=26.0.0`, and npm must satisfy
`<11.10.0 || >=11.17.0`. From the repository root, install the locked graph:

    cd /recovery/hermes-source
    node --version
    npm --version
    npm ci

`npm ci` is required because the desktop build consumes hoisted workspace
dependencies. It uses the committed package-lock.json and may run the
repository's declared install scripts; it does not edit the source checkout's
package manifests.

The agent runs the helper through the complete chain:

    python3 /path/to/package/payload/host/host-patch.py --staged-root /recovery/hermes-source --check
    python3 /path/to/package/payload/host/host-patch.py --staged-root /recovery/hermes-source --apply --through full
    python3 /path/to/package/payload/host/host-patch.py --staged-root /recovery/hermes-source --check

Before any app deployment, the agent runs the desktop checks in the isolated
checkout from the repository root using the workspace's own scripts:

    cd /recovery/hermes-source
    npm run typecheck --workspace apps/desktop
    npm run test:ui --workspace apps/desktop -- --run src/app/chat/composer/hooks/use-composer-voice.test.ts

For an actual unpacked macOS app, use the repository's packaging script after
those checks:

    npm run pack --workspace apps/desktop

That script runs the desktop build and Electron Builder with `--dir
--publish never`. The output is an unpacked app under
`/recovery/hermes-source/apps/desktop/release/`; record the exact `.app` path
reported by the command. The build writes generated files inside the staged
checkout, so the agent records the exact source commit, patch level, Node/npm
versions, install result, command exit codes, and staged app path in the
receipt. No publish command is part of this route. A DMG or zip is a separate
choice using `npm run dist:mac:dmg --workspace apps/desktop` or
`npm run dist:mac:zip --workspace apps/desktop`.

Before relying on the app, verify the resulting bundle with
`codesign --verify --deep --strict --verbose=2 /path/to/Hermes.app`. For local
staged QA, the repository's existing compiled output can be explicitly
ad-hoc signed and rechecked with:

    CSC_IDENTITY_AUTO_DISCOVERY=false npm run builder --workspace apps/desktop -- --dir --publish never --config.mac.identity=-
    codesign --verify --deep --strict --verbose=2 /path/to/Hermes.app

This route was verified for the pinned public base: deep/strict verification
passed, with an `adhoc,runtime` signature, no TeamIdentifier, and 420 sealed
resources. It proves a locally usable bundle and does not make the app trusted
by Gatekeeper or suitable for redistribution. Developer ID signing and
notarization require the member's own Apple credentials and identity; the
package does not invent, borrow, bypass, or weaken those checks. The
repository's notarization hook skips notarization when its Apple credentials
are absent and reports that fact. Treat the local ad-hoc result as a successful
local QA outcome, and fail the redistribution gate unless a valid Developer ID
signature and notarization receipt are present.

## Recoverable app deployment

The staged app is copied or referenced under a recovery directory, for example
/recovery/jarvis/Hermes.app.staged/Hermes.app. The agent verifies it with:

    codesign --verify --deep --strict /recovery/jarvis/Hermes.app.staged/Hermes.app

Deployment is a separate, explicit step after the staged checks. Before it, the
agent preserves the installed app at a timestamped recovery path and records
that the voice call is off. It copies the staged app into the selected member
destination, verifies the signature again, and relaunches only when the member
has authorized that deployment. If the post-deploy receipt or signature check
fails, it restores the preserved app and reports the failed gate.

The helper uses git apply --check before every write and only permits the 16
declared chain paths to change. It does not silently deploy, stop Hermes, or
restart a process.

## Optional Talk presence bus

The original presence patch and its original behavioral tests are retained
under talk-presence/. Use talk-presence-safe.py with a marked staged Talk tree.
It snapshots the staged tree before invoking the original script, rejects
symlinks, detects unrelated deletions or additions, and restores the snapshot
when the original script or its UI build fails. Use --no-build only when the
staged tree's own build is intentionally outside this check. The wrapper's
output is a reversible proof; it never implies that a live call was tested.

The packaged Talk patch inserts one marker-delimited block immediately after
the state hooks in ui/talk-surface.js. It requires these exact anchors:

- SDK.hooks exposes useState, useEffect, useRef, and useCallback.
- TalkPage contains the phase, live, transcript, muted, sleeping, and
  audioActivity state hooks.
- TalkPage contains startTalk, stopTalk, setMuted, and setSleeping.
- The insertion anchor is the appearance state hook immediately after the
  audioActivity hook.

The staged Talk tree must also contain scripts/build_ui.py. When
ui/desktop-entry.js exists, dashboard/dist/style.css must exist because the
builder embeds it. The expected generated outputs are desktop/plugin.js and
dashboard/dist/index.js. Missing anchors or build inputs produce an honest
unsupported result; the wrapper never guesses a newer Talk layout or removes
behavior.

## Dependency notices

Hermes's MIT notice is included at licenses/hermes/LICENSE. Talk's local
distribution license and third-party notice are included at
licenses/hermes-talk/LICENSE and licenses/hermes-talk/THIRD_PARTY_NOTICES.md.
The notices are preserved verbatim from the local read-only source evidence.
