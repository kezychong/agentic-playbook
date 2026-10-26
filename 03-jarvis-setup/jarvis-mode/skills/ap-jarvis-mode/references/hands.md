# Hands agent guide (optional extra, Mac main device only)

Hands let the member's chief of staff read the screen, click and type on the
member's main Mac. It is an optional extra. JARVIS Mode is complete and
supported without it, and it is never offered when the main computer runs
Windows.

Offer hands only after the core JARVIS install has passed its smoke checks.
The agent performs these commands. The member only chooses the devices and
profile, then grants the native permissions when macOS asks.

## Device placement

The headless Hermes computer owns the profile-scoped hands command, config,
state and skill:

```text
<headless profile home>/jarvis/hands/bin/ap-macbook-hands
<headless profile home>/jarvis/hands/config.json
<headless profile home>/jarvis/hands/state/
<headless profile home>/skills/agents/ap-macbook-hands/SKILL.md
```

The member's main Mac owns `CuaDriver.app`, the desktop JARVIS plugin and the
mirror browser profile. Do not swap these roles.

## SSH prerequisites

Before installation, prove that the selected headless host can reach the main
Mac through the member's existing trusted SSH route. The host must already be
in `known_hosts`, key authentication must work in batch mode, and the host
value must be a host name or configured SSH alias rather than an option or a
shell command. The installer and hands command use strict host-key checking.
They do not create keys, accept a new host key or bypass a mismatch.

## Install durable headless hands

Use the selected profile ID, its explicit absolute profile home on the
headless computer, and the verified SSH name of the main Mac:

```bash
JARVIS_HANDS_MINI='headless-host' \
JARVIS_HANDS_PROFILE='selected-profile' \
JARVIS_HANDS_PROFILE_HOME='/absolute/headless/profile-home/selected-profile' \
JARVIS_HANDS_HOSTS='main-mac-host' \
bash payload/bin/install-hands.sh --dry-run
```

`JARVIS_HANDS_MINI` is the computer receiving the profile install.
`JARVIS_HANDS_HOSTS` is the main Mac that CuaDriver controls. When the dry run
shows the intended two devices and profile, run the same command without
`--dry-run`. The default driver path is
`/Applications/CuaDriver.app/Contents/MacOS/cua-driver`; set the absolute
`JARVIS_HANDS_DRIVER` only when discovery proves another installed path.

The installer validates every existing profile-path component before writing,
stages all files, seals one backup-backed transaction and writes a private
receipt. Use the same environment with:

```bash
bash payload/bin/install-hands.sh --check
bash payload/bin/install-hands.sh --undo
```

`--check` writes nothing. `--undo` stops if installed files changed after the
receipt. A new install while a receipt is pending is refused; check or undo the
existing transaction first.

## CuaDriver on the main Mac

The optional helper is a plan by default. Run it on the main Mac:

```bash
bash payload/hands/install-cua-driver.sh --plan
bash payload/hands/install-cua-driver.sh --apply
bash payload/hands/install-cua-driver.sh --undo
```

`--apply` downloads only the pinned official 0.23.2 archive, checks its pinned
SHA-256, signing team and Gatekeeper result, then replaces
`/Applications/CuaDriver.app` through a rollback-backed transaction. `--undo`
requires the current app to match its receipt and consumes that receipt once.
Do not bypass a hash, signature, Gatekeeper, path or changed-app refusal.

## Optional mirror on a second screen

The mirror is a separate optional convenience: the same JARVIS view opened in a
browser window, usually on a second screen. It is not required by hands or by
the core install.

The mirror has no host or port default. Setup must choose one transport:

- `direct`: a verified remote HTTPS dashboard URL.
- `ssh-forward`: an already-running, authenticated SSH forward and its
  explicit loopback HTTP(S) URL. The helper does not start the tunnel.

On the main Mac, use its actual Hermes home:

```bash
HERMES_HOME='/absolute/main-device/HERMES_HOME' \
JARVIS_MIRROR_URL='https://verified-headless-host/mirror-route' \
JARVIS_MIRROR_TRANSPORT='direct' \
payload/bin/jarvis-mirror --dry-run
```

For a verified tunnel, set `JARVIS_MIRROR_TRANSPORT=ssh-forward` and use the
configured loopback endpoint. Optional arguments are `--display NAME`,
`--kiosk`, `--url URL`, and `--transport direct|ssh-forward`. Repeat without
`--dry-run` only after the route, browser profile and display are correct.

`payload/bin/jarvis-toggle` is an optional Mac helper that opens or closes the
JARVIS view. It supports `--toggle`, `--open`, `--close`, `--demo`,
`--keystroke`, and `--dry-run`. The Hermes deep link runs first. The synthetic
keystroke is opt-in and needs Accessibility permission.

## Namespaced frontend receipts

Main-device receipts live under `<main HERMES_HOME>/jarvis/` as
`desktop-heartbeat-<scope>.json`, `desktop-heartbeat-peer-<scope>.json`, and
`hud-heartbeat-<scope>.json`. The scope must exactly match the frontend:

1. Form JavaScript `JSON.stringify([connectionId, route.profile,
   route.targetProfile])`.
2. Run 32-bit FNV-1a over JavaScript UTF-16 code units.
3. Render the unsigned result in lower-case base 36.

Match the receipt's `connectionId` and canonical `profile` to the selected
route. Never fall back to an unsuffixed global heartbeat file.

## Hands smoke checks

Fixture tests and install receipts do not prove hands. When the member takes
this extra, prove it on their real two-device route:

- CuaDriver status plus Accessibility and Screen Recording grants.
- One bounded screen read and one member-approved reversible input action,
  with the no-blind-retry rule preserved.
- If the member also took the mirror, one mirror placement on the selected
  display through its configured authenticated route.
- Receipt-guarded hands and driver undo without harming pre-existing files.

Record the real device, profile, route and receipt. Report any unrun item as
not run rather than inferring it from local tests. A hands failure does not
affect the core install; leave the core in place and report the extra as not
enabled.

### Local Desktop connection identity

The host represents a local profile pool with JSON `connectionId: null`. Preserve that value when matching a receipt. Its scope hashes `[null, routeProfile, targetProfile]`; the string `"null"` is a different identity. For this local-only case, leave `JARVIS_CONNECTION_ID` unset when using `jarvis-toggle` and follow its scoped-receipt discovery hint. Main-to-headless saved connections keep their real non-empty connection ID and the exact hint documented above.
