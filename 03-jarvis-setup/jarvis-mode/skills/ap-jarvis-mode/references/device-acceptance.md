# Release smoke checklist — for the setup agent

Software and synthetic fixtures do not prove the member's live session. Run the
applicable checks below on the member's real devices after staging, and record
the result. Preserve the existing Hermes persona, sign-in and active work. Use a
disposable chat and harmless test content. Record pass, fail or not run; never
turn an unavailable device into a pass.

The core checks are the first two sections. They apply to every supported pair
of computers: a macOS or Windows main computer and a macOS or Linux headless
computer. The hands section only applies when the member took that optional
extra on a Mac main computer.

## Main computer and headless profile

- Confirm the saved connection, route alias and canonical profile. Read authenticated JARVIS settings from that selected profile and match the receipt's connection and profile.
- Open the authenticated browser dashboard for the same profile and confirm its mirror renders and receives current presence.
- Open JARVIS through its normal Desktop action. Observe a real chosen source and its timestamp. Disable an unchosen box; confirm it disappears without removing the central orb, NOW or voice controls.
- Inspect an expanded decision brief, activity updates, the second window and full screen. Reopen the second window after a plugin update.
- Switch between two existing profiles only if the member uses them. Old tasks, voice captions, helpers and selected boxes must not appear in the new profile. Return to the original profile.
- Test a missing or unavailable source using an owned fixture. The view must say what is unavailable and must not display invented data. Restore the fixture afterward.

## Voice

- Use the stock Hermes Desktop call, the round voice button beside the message box, or the Talk plugin when the member already runs it. No host source change is needed for this check.
- In a new disposable chat, start a call through JARVIS and hear one real reply. Ask the chief of staff to identify itself; it must use the member's existing identity.
- Keep the call active through the first answer and one delegated harmless task. Spoken work should produce a short acknowledgement, one long-job helper where appropriate, and a responsive chief of staff.
- Exercise mute/unmute, the supported stop control, end-call, and the corresponding keyboard shortcuts. Confirm the call and microphone stop. A moving orb alone is not proof of working audio.
- Record why a deliberately ended or failed call ended.
- If the member has no voice door available on their host, record that plainly and confirm the face says so instead of pretending. The rest of the install still passes.
- The six call-survival host voice patches are a separate optional Mac extra. If the member took them, verify the host's short-link-interruption behavior and its 15-second recovery window on an isolated test connection: queued work should run once after recovery. Do not interrupt a connection carrying real member work. Record not run when isolation is unavailable. During a link cut some on-screen controls can be unavailable, so verify the supported keyboard/stop route as well.

## Hands (optional extra, Mac main computer only)

Use [hands.md](hands.md) for the exact setup and transport contract. Prove a harmless screen read, click and typed test text on the selected main Mac, permission denial, and a blocked unsafe request. Do not enable macOS permissions programmatically. Verify the driver identity and the profile-specific command path.

Skip this whole section when the member's main computer runs Windows or when the member declined the extra, and record it as not applicable. A hands failure never invalidates the core install.

## Recovery and receipt

Use the recorded undo path for an owned installation test. Confirm the old files and directory modes return and that the member's persona and unrelated files remain untouched. If member-edited files prevent safe undo, preserve them and report the exact recovery path.

Keep a local receipt with package digest, host version, device roles and operating systems, canonical profile, chosen boxes, checks and undo result. Do not include credentials, raw conversations or personal source content in a shared receipt. A failed or not-run optional check is reported as exactly that; it does not invalidate the truthful core evidence.
