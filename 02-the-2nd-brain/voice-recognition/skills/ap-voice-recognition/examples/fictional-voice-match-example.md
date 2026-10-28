# Fictional walkthrough: a low-confidence voice match

Agentic Playbook — by Kezy · Fictional sample, not an executed test

## Input

Two saved, human-approved voice profiles exist: "Alex" and "Priya," each created from a sample the
human personally confirmed. A 15-second voice sample from a fictional recorded call needs to be
checked against them.

## Comparison result

| Profile | Score |
|---|---|
| Alex | 0.58 |
| Priya | 0.54 |

Both scores sit below the configured confidence threshold (0.75), and they are close enough to each
other that neither stands out. Per the process, this is reported as "no confident match," not as a
guess toward Alex because the score is marginally higher.

## Report to the human

> No confident match for this sample. Closest candidates: Alex (0.58), Priya (0.54), both below
> threshold. This may be a third, unregistered speaker, or the sample quality may be too low to tell
> Alex and Priya apart. Recommend a longer or cleaner sample, or your own direct identification.

## Human answer (fictional)

The human listens and says: "That's Alex, I recognize his voice directly — go ahead and mark it."

## Outcome

The match is recorded as confirmed by direct human identification, not by the voice-comparison score,
and logged as such:

```markdown
- Sample from 2026-10-04 call, segment 00:04:12-00:04:27 → Alex
  (confirmed by: human direct identification; comparison score was below threshold and was not the
  basis for this match)
```

## Negative check

If the human had instead said "I'm not sure either," the result stays "no confident match," the
segment is left unattributed in any downstream transcript or minutes, and no profile is created or
guessed from the call content alone.

<!-- Agentic Playbook — by Kezy -->
