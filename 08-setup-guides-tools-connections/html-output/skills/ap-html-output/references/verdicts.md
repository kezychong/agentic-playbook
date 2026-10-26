# Verdict cards and copy-back

Use this reference whenever a page asks a person to review, confirm, veto, edit, or supply a safe input.

## Card contract

One decision gets one card. Keep the full decision on the page.

Each card has:

1. a stable ID such as `D1`;
2. a question in plain words;
3. the complete proposal or draft;
4. what Confirm means;
5. what Veto means;
6. what Edit changes;
7. three radio controls: Confirm, Veto, Edit;
8. no preselected radio;
9. an optional note textarea;
10. a visible current state such as Unanswered.

The page may recommend a choice. The recommendation is not the member’s answer.

Veto must say what stops, stays manual, or remains undefined. Never turn Veto into automatic execution. Edit means the note carries a replacement scope, rule, or target.

## Safe data asks

Put a missing-data field beside the decision it informs. State:

- the exact value needed;
- why it matters;
- the allowed range or format;
- what a blank value means;
- what the page will not collect.

Never ask for passwords, API keys, card details, access tokens, or confidential account data. Use a safe setup status or an approved secret tool instead. Keep secret values out of page text, notes, outputs, and clipboard content.

## Copy-back block

The single primary button is labeled “Copy my verdicts.” It creates a Markdown block that contains:

- page version;
- source basename;
- local copy date;
- safe data fields and whether each was supplied;
- every decision ID;
- every full question;
- every full proposal;
- Confirm, Veto, and Edit meanings;
- the chosen answer or `Unanswered`;
- every note;
- a machine-readable JSON object.

Encode every note as a JSON string with `JSON.stringify`. This keeps quotes, newlines, pipes, angle brackets, and punctuation as data. Put the result in a readonly textarea for inspection.

Example shape:

```text
# HTML Output verdicts

- Page version: 2.0.0
- Source basename: demo.html
- Local copy date: 2026-09-15
- Weekly time budget (minutes): not supplied

## D1: Try reply drafts first?

- Answer: Unanswered
- Proposal: A bounded seven-day test.
- Confirm means: Start only that bounded test.
- Veto means: Keep the current manual workflow.
- Edit means: Replace the scope in the note.
- Note (JSON string): ""

## Machine-readable answers

{
  "page_version": "2.0.0",
  "source_basename": "demo.html",
  "local_copy_date": "2026-09-15",
  "safe_fields": {"weekly_time_budget_minutes": null},
  "decisions": [{"id":"D1","answer":"Unanswered","note":""}]
}
```

Do not execute the answer while building the block. The block is a handoff for the member’s next agent turn.

## Clipboard behavior

Use a small helper with two outcomes:

1. If `navigator.clipboard.writeText` resolves, show a success message.
2. If clipboard access is missing or rejected, focus and select the full readonly textarea, then show: “Clipboard unavailable or refused. The full text is selected. Copy it manually.”

Do not show “Copied” before the write resolves. Do not silently discard the text.

Both copy controls validate the safe fields before writing. A nonblank invalid value, including a native number input `badInput`, blocks both buttons. A truly blank field remains valid and is copied as `not supplied`.

Build the copy date from local calendar parts rather than locale text or UTC:

```js
function localDate(){
  const now = new Date();
  const pad = value => String(value).padStart(2,'0');
  return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
}
```

When a choice, note, or safe field changes, clear both copy-status messages. Track the current form snapshot while a clipboard Promise is pending. If the form changes before it resolves, do not show success for the old snapshot; tell the member to copy the changed block again.

Use `.value` for textarea content and `textContent` for status messages. Do not insert notes or generated output with `innerHTML`.

## Copy as prompt

Provide a second working control labeled “Copy as prompt.” Its output contains:

- the original kickoff ask;
- the page’s purpose;
- the source basename and version;
- the safe inputs;
- the full decision questions and proposals;
- a request to continue only after reading the member’s copied verdicts.

The prompt must not execute a choice or imply that an unanswered choice was confirmed.

## State and storage

Keep choices in live form controls until the member leaves or refreshes the page. Do not use local storage unless a separate brief explicitly authorizes it. The page must say that refreshing clears answers.

Do not send data over the network. Do not add analytics, tracking, auto-send, silent uploads, or hidden remote storage.

## Validation

Validate safe fields before building the output. For a whole-number minute field, accept blank or a non-negative integer within a sensible maximum. Show the error beside the field and focus it. A blank field becomes `not supplied`, never zero.

The choice controls themselves do not execute any action. They only change what is copied back.

## Review checklist

- [ ] Full proposal is visible.
- [ ] Confirm consequence is visible.
- [ ] Veto consequence is visible.
- [ ] Edit rule is visible.
- [ ] Every card starts Unanswered.
- [ ] Every note is included.
- [ ] Notes are JSON-string encoded.
- [ ] Unanswered cards remain in the output.
- [ ] Source basename and page version are included.
- [ ] Local copy date is included.
- [ ] Safe field values are included.
- [ ] Clipboard success is honest.
- [ ] Manual-copy fallback selects the full output.
- [ ] No secret field exists.
- [ ] No choice executes from the page.
