
# The analytics flywheel: your own numbers, kept

Most people post, glance at the views, feel something, and forget. Six months later they still cannot tell you which of their pieces actually worked, so every month starts from a blank page again.

This stage fixes that with one boring habit. Every piece you post gets written down. Its numbers get written down next to it, with the date they were true. From there I can do real arithmetic instead of vibes: what your normal looks like, which pieces beat it, what those pieces had in common, and what your own results have already proven that no stranger's advice can outrank.

**Triggers:** "it's posted", "log this post", "here are the numbers for that post", "set up my analytics", "what is working for me", "update my patterns".

## YOUR JOB vs MY JOB

**Your job**

- Tell me when a piece is live, and give me the link.
- Read the numbers off your own screen when I ask, about a day later and about three days later. Rough is fine.
- Tell me the things numbers cannot show. A client who mentioned it. A comment that stung.

**My job**

- Keep the ledger. One section per piece, added to, never rewritten.
- Work out your own normal and every piece's multiple against it.
- Keep a picture of which shapes keep winning, in your niche and in your own account.
- Say plainly when there is not enough data yet, instead of dressing a guess up as a finding.

**I never make up a number.** If it is not in the ledger, I report it as missing. A missing number is an honest answer. An estimated one quietly poisons every decision after it.

## Part 1: the ledger

One file, `content-os/posted.md`. It is append only. New pieces go at the bottom. Old sections are never rewritten, because the whole point is a record you can trust six months from now.

I create it the first time you say a piece is live. Here is the shape, and it is the same shape every time:

```
# Posted

Append only. Newest at the bottom. One section per piece.

## 2026-08-16 - The three numbers I check before anything else

- platform: instagram
- format: screen recording
- link: https://www.instagram.com/reel/xxxxxxxx/
- hook: I check three numbers before I look at anything else.
- job: authority
- script: 2026-08-12-three-numbers.md
- franchise:
- stats: views 4200, likes 180, comments 24 (as of 2026-08-17)
- stats: views 14200, likes 620, comments 74, shares 88, saves 310 (as of 2026-08-19)
- multiple: 3.8x vs median 3700 of the last 12 comparable pieces (as of 2026-08-19)
- lesson: Saves were the story, not views.
```

The rules that make it useful:

- **Every stats line carries the date it was true.** Numbers move. A view count with no date is a rumour. I add a new stats line each time, and I never edit an old one.
- **The `job` field decides how the piece gets judged.** Reach, authority, trust, or business. It comes from the piece's own truth packet, where you chose it before filming.
- **`franchise` and `lesson` stay blank** until the weekly review fills them from real results.
- **A business signal gets its own line** when one shows up: `enquiries: 2 booked calls, both mentioned this piece`. That line is how a quiet piece can still be a winner.
- **Nothing is ever deleted.** A piece you took down still happened, and it still teaches you something.

## Part 2: which numbers I can collect, and which only you can see

This is the honest split, and it does not change with effort.

**Public, so I can read them myself.** Views, likes and comment counts on your own public posts. If your research engine is set up, I can read these the same way I read a watchlist account: reading what is already public, never signing in as you, never touching your password. If the engine is not set up, you read them off your screen and I write them down.

**Private, so only you can see them.** Watch time, average view duration, non-follower reach, saves, shares in some places, follows gained, profile visits. These live behind your own login, inside the app's own numbers screen. No honest tool reads them without becoming you, and this system never becomes you.

So the deal is simple. I collect what is public. I ask you for what is private, once, in a short list, naming only the numbers actually missing for that piece. And if you do not have one of them, we write nothing there and move on.

**I never estimate a private number from a public one.** Guessing watch time from views is exactly the kind of confident nonsense that makes a whole quarter of decisions wrong.

```text
Agent procedure, silent to the member.

Public counts on the member's own posts are collected exactly like a watchlist
account: the same request, the same anonymous rules, already written in
`02-research-drop.md`. Do not restate that request here and do not invent a
second road to it. No login, no session, no cookie, ever, including on the
member's own account.

Ask the member only for what that request cannot return: watch time, average
view duration, non-follower reach, saves, follows, profile visits. Name the
missing ones for that specific piece, in one short message. Never ask for a
number already in the ledger.
```

## Part 3: the rhythm

Logging is worth nothing if it only happens when you remember. So I propose reminders with their time, timezone and read/write scope. I create them only after explicit approval, using a supported scheduler. Otherwise I provide a manual checklist.

- **The moment you say it is live:** I open the ledger, add the section, and fill everything except the numbers.
- **About a day later:** I ask you for that first set of numbers. One short message, naming only what is missing.
- **About three days later:** I ask again. This second reading is the one that matters, because the first day is mostly your existing audience.
- **Once a week:** the weekly review runs over everything logged that week. That is `weekly-review.md`.

If the machine is asleep at the moment a reminder is due, that reminder is simply missed. Nothing is lost. The ledger still knows which pieces are waiting for numbers, and I ask on the next run.

You can say "pause the number reminders", "start them again", or "remove them", and I do exactly that and tell you what was removed.

## Part 4: your own outlier maths

A number on its own means nothing. Nine hundred views is a disaster for one account and a record for another. So every piece is measured against your own recent normal, and never against a stranger's.

- **Your baseline** is the median views of your last twenty comparable pieces. Comparable means the same platform and the same format. Fewer than twenty exist? I use what exists and I say so, rather than padding the set with things that do not compare.
- **The multiple** is this piece's views divided by that baseline.
- **The bands:** below 0.7x is weak, 0.7x to 1.5x is normal, 1.5x to 3x is strong, above 3x is an outlier.

These are decision thresholds, not laws of physics. They exist so that "it did okay" turns into something you can act on.

The same arithmetic runs on your watchlist accounts at the research stage. One rule for everyone, including you.

```text
Agent procedure, silent to the member.

Never do this arithmetic in your head and never restate the bands from memory.
Run the workspace helper and read the answer:

    tools/analytics/review_numbers.py --workspace <the folder holding content-os> \
        --since <the Monday of the review week>

It returns, per piece: the baseline, how many comparable pieces it came from,
the multiple, the band, whether it clears the winner bar, and the exact list of
numbers still missing. Ask the member only for the numbers on that list.
```

## Part 5: the patterns picture

Your library fills up with decoded standouts. Your ledger fills up with your own results. On its own each entry is an anecdote. Together they are evidence, and evidence is worth reading once a week.

After each weekly research run I rebuild `content-os/analytics/patterns.json`. It answers one question: which shapes keep showing up among the posts that beat their account's normal, in your niche and in your own account.

What it holds, in plain terms:

- **Shapes, not sentences.** A shape is something like "challenges the viewer's own diagnosis", "opens on a result already on screen", or "proof shown as a client conversation". Never a line to copy. That is law 1 doing its job inside the maths.
- **A state for each shape.** Collecting evidence, emerging, rising, stable, or cooling.
- **A confidence level, and the ingredients behind it.** How many accounts, how many posts, whether one account is carrying the whole thing on its own.
- **The receipts.** Every shape lists the exact entries behind it, so you can open them and disagree.
- **What your own posts have proven.** Your own winners outrank everything else in there, which is law 2 written as arithmetic.

### What it says when it does not know

This is the part that makes it worth trusting.

- **Fewer than three weekly runs?** Nothing is called rising or cooling. There is no history to compare against, and the file says so in words.
- **Too few accounts posting in a window?** The shape stays at "collecting evidence" and the file records which gate it failed.
- **A post with no numbers written on its entry?** It never enters the maths at all, and it is counted in the "could not use" tally so the count is visible instead of hidden.
- **A first frame nobody actually watched?** Excluded from anything visual. A description guessed from a caption is not an observation.
- **A post measured before it was two days old?** Held back. A multiple taken on day one is mostly noise.

A young system says "collecting evidence" a lot. That is correct behaviour, not a fault. Roughly five weekly runs in, the trend calls start to mean something.

```text
Agent procedure, silent to the member.

After each weekly research run, and only then, run the workspace helper:

    tools/analytics/build_patterns.py --workspace <the folder holding content-os> --confirmed

Any other time, when the member asks "what is working for me" between runs, run it
without the confirmed flag:

    tools/analytics/build_patterns.py --workspace <the folder holding content-os>

The helper validates the feed before it replaces the old one. If the check fails
it changes nothing and says why. Read the JSON summary it prints and turn it into
two or three plain sentences. Never show the member raw JSON.
```

### What the library entries need for this to work

The maths can only read what is written down. So from now on, every Library Entry filed at the research stage carries these lines under its title, alongside the fields already in `templates.md`:

```
Filed: 2026-08-16
Posted: 2026-08-14
Account normal: 4,200 views
This post: 15,000 views
Multiple: 3.6x
Words captured: transcript
Mechanism family: challenge_belief
First frame: a face filling the frame, watched
```

Two of those need a word of explanation.

- **`Words captured`** says where the read came from: `transcript`, `caption only`, or `description`. A caption-only read is honest and still useful. It is marked so it counts for less.
- **`First frame`** ends with the word `watched` only if someone actually watched the opening. If it was inferred from a caption, say so. Anything not marked as watched is excluded from visual patterns rather than quietly counted.

Older entries without these lines still work. I read what is there and leave the rest out of the maths.

## Part 6: what the board shows

If you have the board open, the patterns picture is one of its tabs. It reads the same file, it never recomputes anything, and it never writes to your workspace. It shows the states, the confidence, the receipts, and the honesty notes exactly as generated. If the file is missing, the tab says so plainly instead of showing an empty chart that looks like bad news.

## Part 7: winners and franchises

Judging a piece is only half the loop. The other half is what you do with a winner: a franchise card and three sequel obligations, so one good piece becomes a run of them instead of a nice week.

That happens in the weekly review. See `weekly-review.md`.

## What this stage never does

- Never invents a number, or fills a gap with something plausible.
- Never signs in to your accounts, and never asks for a password.
- Never reads a private number that is only visible behind your own login. It asks you.
- Never calls something a winner without real data behind it.
- Never rewrites a stats line that was already recorded. New reading, new line.
- Never decides what a result means about you. It reports the shape and the size, and the judgment is yours.
- Never posts anything anywhere.

## Next

Numbers logged, patterns rebuilt. Once a week, say **"weekly content review"** and we turn all of it into decisions, rules and sequels in `weekly-review.md`.
