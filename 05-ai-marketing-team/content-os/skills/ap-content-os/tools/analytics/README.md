# tools/analytics

Agent-facing notes. The owner never opens this folder and never runs anything here. The agent does.

Everything is standard library only. No packages to install, no network calls, no keys, nothing written outside the owner's `content-os/analytics/` folder.

## The four files

| File | Job |
|---|---|
| `outlier_math.py` | One post's views divided by an account's median, with a 3x flag and a recency note. Used for watchlist accounts at the research stage and for the owner's own posts at the weekly review. Do not reimplement this arithmetic anywhere else. |
| `review_numbers.py` | Reads `content-os/posted.md` and returns, per piece, the baseline, the multiple, the band, the winner test, and a list of the numbers that are missing. Calls `outlier_math.py`. |
| `build_patterns.py` | Reads the library, the research state, the watchlist and the ledger, and writes `content-os/analytics/patterns.json`. Keeps weekly snapshots in `content-os/analytics/pattern-history.json`. |
| `feed_contract.py` | Checks the feed against `schemas/patterns-feed.schema.json` plus the cross-record rules. `build_patterns.py` refuses to replace a good file with a feed that fails this check. |

## Running them

```bash
# after the weekly research run, from the folder that holds content-os/
python3 tools/analytics/build_patterns.py --workspace . --confirmed

# any other time, an in-between build that does not create a weekly snapshot
python3 tools/analytics/build_patterns.py --workspace .

# the weekly review numbers, for the last seven days
python3 tools/analytics/review_numbers.py --workspace . --since 2026-08-17
```

Both print JSON to stdout for the agent to read. Neither prints anything the owner should see raw. Translate it into plain sentences.

`--confirmed` matters. It marks the build as the weekly one: it records a snapshot, so streaks, persistence and cooling can be measured, and it is the only kind of build that produces Test-next cards.

## Tests

```bash
cd tools/analytics && python3 -m unittest discover -s tests -p "test_*.py"
```

64 tests. `tests/make_synthetic_workspace.py` builds a made-up workspace in a temporary folder. Never point it at a real one.

## The posted-content ledger, for anyone else reading it

`content-os/posted.md` is append-only heading markdown, no frontmatter. One `## YYYY-MM-DD - title` section per posted piece, then bullet fields:

```
## 2026-08-16 - The three numbers I check before anything else

- platform: instagram
- format: screen recording
- link: https://...
- hook: the exact opening line used
- job: reach | authority | trust | business
- script: 2026-08-12-three-numbers.md
- franchise: (blank until the weekly review names one)
- stats: views 4200, likes 180, comments 24 (as of 2026-08-17)
- stats: views 14200, likes 620, saves 310 (as of 2026-08-19)
- multiple: 3.8x vs median 3700 of the last 12 comparable pieces (as of 2026-08-19)
- lesson: one line, written at the weekly review
```

Read it defensively. The file may not exist. Any field may be missing. `stats` repeats, oldest first, and each line carries its own as-of date, so never treat the first one as current. `workspace_read.read_posted_ledger()` already does all of this; import it rather than writing a second parser. The full rules live in `references/09-analytics-flywheel.md`.

## Notes for whoever builds the board

- The feed is `content-os/analytics/patterns.json`. Read that file. Never read the markdown workspace to recompute patterns.
- Field names match the original feed the board was written against, including `freshness.w2_last_success`, which means "the last successful research run". One field was renamed: the blank-angle field on a Test-next card is `owner_angle`, and it is always an empty string. The owner's angle is never machine-written.
- **Research runs weekly, not nightly.** A staleness rule written for a daily scan will mark this feed stale forever. Ten days is the sensible line here.
- Absence is normal. There may be no feed at all, or a feed with zero patterns. Show an honest empty state, never a placeholder number.
- `quality.scan_exceptions` is a list of plain-English honesty notes. Show them.
- `provisional: true` means this build happened between weekly runs. `views.rising` and `views.cooling` are empty until three weekly snapshots exist, and `gate_receipt.scan_state` says `unmeasured` while that is true.
