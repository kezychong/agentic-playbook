# Rubric — <loop name> / <stage name>
<!-- THIS IS THE ASSET. The loop-spec says who does what; this file says what "good" means. Every item is a concrete yes/no you could check in five seconds without arguing. Vague items ("is it engaging?") don't belong here — rewrite them until they're testable. Every time you reject something the worker made, a new item gets added below so the same mistake never reaches you twice. Lives at ./loops/<loop-name>/rubric.md. -->

Every item must PASS. Any FAIL sends the work back to the worker.

**Output this grades:** <the exact thing the worker produces for this stage>
**Worker:** <model/tool>  **Checker:** <a SEPARATE model/tool — never the worker grading itself>
**Last updated:** <YYYY-MM-DD>

---

## Checklist
<!-- 5–10 concrete pass/fail rules. Each is a yes/no the checker can mark without guessing. -->
- [ ] <e.g. No claim that isn't on the confirmed-facts list>
- [ ] <e.g. First line names a specific pain or outcome, not a generic statement>
- [ ] <e.g. One idea only — no second topic smuggled in>
- [ ] <e.g. Mentions the offer exactly once, never twice>
- [ ] <e.g. Has a clear single call-to-action>
- [ ] <e.g. Zero placeholder text left in ("[insert X]", "lorem", "TODO")>
- [ ] <add your non-negotiables — keep each one testable>

## Notes
<!-- Any context the checker needs to judge fairly. -->
<e.g. "Confirmed-facts list lives in the brief the human provides each run.">

## Verdict format
<!-- What the checker returns. Keep it mechanical so it's easy to act on. -->
```
VERDICT: PASS | FAIL
Failed items: <name each item that failed, or "none">
Fix next: <one line per failed item, plain instruction>
```

---

## Learned from feedback
<!-- This is how the loop gets SMARTER. Every time you reject output the checker passed (or you catch something the rubric missed), append a dated line AND add the matching item to the Checklist above. The rule: a mistake you've corrected once should never reach you again. Newest at top. -->
- <YYYY-MM-DD> — FAIL if <what was wrong>. Added checklist item: <the new yes/no line you put above>.
- <YYYY-MM-DD> — Rubric created with <N> checklist items.
