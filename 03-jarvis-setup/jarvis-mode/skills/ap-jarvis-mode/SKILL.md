---
name: ap-jarvis-mode
description: "Plan an optional profile-scoped JARVIS command centre."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Agentic Playbook JARVIS Mode

Version 0.1.0, runtime untested. The proposed core install is the JARVIS face on the member's main computer, the JARVIS backend on the member's headless Hermes profile, and voice through the Hermes Desktop app's own call button. Hands and the host voice patches are optional extras for a Mac main device; they are offered only after the core install works and they never gate it.

## Who this is for

This skill is for a member who already uses Hermes as a chief of staff through the Claude app or Codex app and wants a JARVIS-style command centre on their main computer. The agent owns setup, checks dependencies, and explains the required permission clicks that the member must make. The member does not need to know technical setup steps.

## Platforms this version covers

- **Main computer:** macOS or Windows, running the Hermes Desktop app. Detect which one before planning any path.
- **Headless computer:** macOS or Linux, running the member's Hermes chief-of-staff profile.
- **Hermes home:** `%LOCALAPPDATA%\hermes` on Windows (per the Hermes Desktop README) and `~/.hermes` elsewhere. Treat those as the shape of the answer, never as the answer. The destination is always discovered from the member's real host and confirmed by the member.
- **Optional extras, Mac main device only:** hands through CuaDriver, and the six call-survival host voice patches. Skip both on a Windows main device and say so plainly.
- **Honesty about proof:** the supplied source describes Mac and Linux testing, but no runtime or hardware testing was performed for this adapted package. Windows is a design target only, so report a Windows result as what the agent actually observed on the member's machine, never as a pre-existing guarantee and never as a refusal.

## Operating contract

- Preserve the member's existing persona, authentication, chats, profile and operating rules. Add JARVIS guidance; never replace identity files.
- Detect the operating system of both roles before planning any destination, command or extra. Never assume the main computer is a Mac.
- Discover the member's existing profile, devices, timezone and source locations. Never inherit another person's names, paths, credentials, labels or records.
- Ask which information boxes the member wants. Keep every original box available when its source is present; label a missing, stale or unreachable source plainly.
- Connect only to the member's authenticated Hermes host route. Do not create a public server, bypass a host check, or copy credentials into the package.
- Stop before writing if `install_ready` is false, a required component is absent, the selected profile cannot be confirmed, or a native permission is unavailable. A stop leaves zero destination writes.
- Voice in the core install is the Hermes Desktop app's own call, or the Talk plugin when the member already has it. The core install never waits on a host patch. If no voice door exists on the member's host, leave the face honest about it and finish the rest of the install.
- Offer the optional Mac extras only after the core smoke checks pass, one at a time, each clearly labelled optional. A member who declines every extra still has a complete install.
- Keep spoken replies short and delegate one long job when appropriate. Keep the chief of staff responsive during calls.
- Preserve honest unavailable states. Never fabricate activity, metrics, finance readings, calendar entries or brain content.

## Setup sequence

1. Run package preflight. Proceed only on `PASS RELEASE` with `install_ready: true`. Stop with zero destination writes otherwise.
2. Detect both operating systems: the main computer (macOS or Windows) and the headless computer (macOS or Linux). Record both. They decide the path shapes, the shortcut labels and which extras may be offered later.
3. Discover the Hermes home and the headless profile home on the member's real hosts, then have the member confirm them. Use the platform shape above as a hint only; do not guess, hardcode or carry a path from another machine.
4. Confirm the member's profile identity and existing authentication before provisioning profile-scoped configuration.
5. Ask which boxes to enable in the member app, offering the complete available set by default. Ask where a chosen box's real source lives when discovery cannot find it.
6. Install only the exact verified files for the chosen role, recording a receipt and preserving backups.
7. Pass the member's chosen boxes and source locations to the setup entrypoint. It validates the profile-scoped schema through the packaged backend and writes only the selected profile's configuration.
8. Enable voice through the stock Hermes Desktop call, the round voice button beside the message box, or through the Talk plugin when the member already runs it. No host source change is required and none is attempted here. Explain the microphone permission at the moment the operating system asks.
9. Run the member's smoke checks: open the main view, start and end a voice call with the built-in voice button, observe one real selected source, and confirm an unavailable source is labelled honestly.
10. Report the installed role, receipt, checks and undo path. Only then, and only on a Mac main device, offer the optional extras: hands through CuaDriver, and the six call-survival host voice patches. Explain the screen-control and second-display permissions at that point, not before.

## Box and source contract

Ask the member to choose from these visible boxes: `agent_helpers`, `waiting_on_you`, `agent_in_flight`, `overnight_jobs`, `next_meeting`, `today`, `spend`, `scoreboard`, and `fleet`. Keep `waiting_on_you` and `agent_in_flight` as separate choices. `NOW` and voice controls stay available. `fleet` is host data and has no backend source ID.

The backend source IDs are `agent_state`, `agent_helpers`, `next_meeting`, `today_plan`, `overnight_jobs`, `one_thing_scoreboard`, `spend`, `lever`, `brains`, `scoreboard`, and `log`. They are source adapters, not assumptions about the member's visible labels. Only enabled sources may read data or start helper work.

The visible box inventory is part of the supplied, unexecuted payload. Do not invent a substitute interface or silently remove a box; mark its source missing or unavailable when the member has not configured it.

## Agent handoff for the two devices

The following is the technical handoff for an agent working from the member's Claude app or Codex app. It is deliberately separate from the member instructions above.

1. Ask the member which boxes to enable, then pass the selected IDs and discovered source locations to `scripts/install.py --setup`. The script validates the choices; it does not conduct the member conversation.
2. On each device, discover the existing Hermes profile with the host's profile matcher, `profile_matches_home(profile_id, profile_root)`. Treat that host result as the identity proof. A directory basename alone is not proof, including for the `default` profile or a custom Hermes home.
3. Transfer the package over the member's existing trusted SSH route. Verify the package digest on both devices and run the full package preflight on both before any import or write. Do not copy credentials, private records or a new persona.
4. Run the `main` role on the selected main-computer destination, which may be macOS or Windows. Run the `headless` role on the selected existing profile destination, which may be macOS or Linux. Pass the same profile ID that the host matcher confirmed.
5. In the confirmed profile context, use the Hermes CLI's documented form `hermes -p <profile-id> plugins enable <plugin-name>` (or omit `-p` only when the confirmed profile is the active default). Confirm the exact plugin name from `hermes plugins list`; do not guess it. This form is the same on every supported platform.
6. Restart only the discovered dashboard owner, and only when there is no active call or turn. Do not guess a launch-service label. Reconnect or reopen the peer windows after the owner is back.
7. Prove the result through an authenticated status/settings response whose `profile_id` matches the selected profile. A local receipt, file hash or fixture pass is useful installation evidence but is not live device proof.
8. Only after step 7 passes, and only when the main computer is a Mac, offer the optional extras. Hands follow [references/hands.md](references/hands.md). The six call-survival voice patches follow [payload/host/host-compatibility.md](payload/host/host-compatibility.md) and require its exact-source proof; without that proof, report the extra as unavailable and leave the working stock call in place.

This version covers a macOS or Windows main computer and a macOS or Linux headless computer. These are source design targets only. This repackage has no Mac, Linux, Windows or two-device runtime evidence; validate on the selected host before claiming compatibility.

## References

Read [references/install-contract.md](references/install-contract.md) before changing installation behavior. It defines the preflight, mapping, backup and undo rules.

Also read [references/configuration.md](references/configuration.md) for the profile-scoped schema, and [references/hands.md](references/hands.md), [payload/host/host-compatibility.md](payload/host/host-compatibility.md) and the [optional hands notice](payload/hands/cua-driver-notice.txt) before offering either optional extra.

Run [references/device-acceptance.md](references/device-acceptance.md) as the release smoke checklist after staging.
