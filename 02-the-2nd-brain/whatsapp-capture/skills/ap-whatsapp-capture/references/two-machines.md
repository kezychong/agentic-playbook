---
stage: shipped
---

# Two Machines: Mac Mini Version and VPS Version

Same method on both. Only the browser and the QR link differ.

## Mac mini version

**Browser.** Open WhatsApp Web (web.whatsapp.com) in its own browser window with its own saved profile.
Keep that profile only for this skill, so it stays signed in and nothing else touches it.
Leave the window open. Tell the member: "Please never close the WhatsApp window on your Mac mini."

**Link.** Show the QR code on the Mac mini screen. If the member is not at the Mac mini, take a picture of the code and send it in chat.
The member scans it: WhatsApp, Settings, Linked devices, Link a device.
Wait for them to reply OK. Confirm the chat list has loaded before you continue.

**Schedule.** Set a scheduled job on the Mac mini that runs every two hours. It starts the agent on the Mac mini with "Run my WhatsApp capture now" and this skill.
Each run: open that same browser profile, run the health check, then capture.

## VPS version

**Browser.** A VPS has no screen. Use a headless browser (a browser that runs without a window) with a saved, persistent profile on the VPS.
The persistent profile keeps the link after the browser closes or the VPS restarts. Never use a throwaway profile, or the member must re-link every run.

**Link.** Open WhatsApp Web in the headless browser. Take a picture of the QR code and send it to the member in chat.
Say: "Scan this within about a minute: WhatsApp, Settings, Linked devices, Link a device. Reply OK when done."
The code expires quickly. If it expires before they scan, take and send a fresh one. Stop after three tries and ask when they have a minute.
Confirm the chat list has loaded before you continue.

**Schedule.** Set a scheduled job on the VPS that runs every two hours. It starts the agent on the VPS with "Run my WhatsApp capture now" and this skill. If the member's agent is Hermes, use its scheduled jobs.
Each run: start the headless browser with the saved profile, run the health check, capture, then close the browser.

**Getting notes to the laptop.** Write into the second brain inbox on the VPS.
The member's existing second brain sync carries the notes to their laptop. If their second brain has no sync, tell them in one sentence that notes stay on the VPS until sync is set up.

## When a run fails

| What you see | What you do |
|---|---|
| QR code, "logged out", or "phone not connected" | Stop. Record the time. Send the one-sentence re-link message once. Pause the capture until they re-link. |
| Page will not load | Try once more on the next scheduled run. If two runs in a row fail, tell the member once. |
| A chat name changed | Keep the old note. Start a new note under the new name and add a line in both pointing to each other. |
| Two chats share a name | Add a short detail to the second file name, for example the group size or first message date. Never a phone number. |
