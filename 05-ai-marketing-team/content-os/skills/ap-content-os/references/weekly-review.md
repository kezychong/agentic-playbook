
# Weekly review: twenty minutes that make next month better

Once a week we sit with what actually happened. I already hold most of it, because every piece you posted went into your ledger with its numbers and the dates they were true (`09-analytics-flywheel.md`). So this is not a data entry session. I bring the arithmetic and the receipts, you bring the things numbers cannot see, and we leave with rules, sequels, and a decision about what gets made next.

**Triggers:** "weekly content review", "here are my numbers", "what worked this week".

## YOUR JOB vs MY JOB

**Your job**

- Fill the short gaps I name. Usually two or three numbers only you can see.
- Tell me what the numbers do not show. A comment that stung. A client who mentioned a piece. A reply that told you something.
- Confirm or reject each lesson before it becomes a rule.

**My job**

- Read the ledger first, and only ask you for what I genuinely cannot see.
- Judge every piece against the job it was actually built for.
- Diagnose the shape of the numbers, not the raw number.
- Spot the winners and log what they owe you.
- Write confirmed lessons into `MY-RULES.md` so I stop repeating mistakes.

**I never make up a number.** If something is missing after I have asked, I write "unattributed" and move on. A missing number is an honest answer. An estimated one quietly poisons every decision after it.

## Step 0: I read before I ask

Before I say anything I read three things.

1. **`content-os/posted.md`**, your ledger. Every piece from the review window, its numbers, and the date each reading was taken.
2. **`content-os/analytics/patterns.json`**, if it exists. What has been recurring lately among the standouts in your niche, and what your own results have already proven.
3. **`MY-RULES.md`**, so I judge this week by the rules you have already given me.

Then I ask you for the gaps, in one short list, naming only the numbers actually missing. Usually that is watch time, non-follower reach, saves, follows, or profile visits, because those live behind your own login and no honest tool can read them. If you do not have one, we leave it blank.

```text
Agent procedure, silent to the member. Run the workspace helper:

    tools/analytics/review_numbers.py --workspace <the folder holding content-os> \
        --since <the start of the review window>

Use its output as the source of every number in this review. It returns, per piece:
baseline, how many comparable pieces that baseline came from, multiple, band,
the winner test, and the exact list of missing numbers. Ask only for that list.
Never restate a band from memory and never do the arithmetic by hand.

If content-os/posted.md does not exist yet, say so plainly, offer to start it,
and run this review from what the member pastes instead. Never invent a history.
```

## Step 1: name the job before you judge the piece

Every piece was built for one of four jobs, and the job decides which numbers matter. I take it from the ledger, where it was recorded when the piece went live.

- **Reach.** Non-follower views, shares, watch time, follows.
- **Authority.** Saves, profile visits, thoughtful comments, people quoting your framing back at you, invitations.
- **Trust.** Messages, personal comments, returning viewers, real conversation.
- **Business.** List sign-ups, enquiries, bookings, sales, trials.

**Never one number for everything.** A story built for trust and a teardown built for authority do not get graded on the same curve. A wedding photographer's raw story about a wedding she nearly ruined can pull half the views of her lighting tutorial and still be the better piece that week, because it was doing a different job.

## Step 2: the multiple, against your own baseline

Each piece is measured against your own recent normal, never against a stranger's numbers.

Your baseline is the median views of your last twenty comparable pieces. Comparable means the same platform and the same format. Fewer than twenty exist? I use what exists and I say so, rather than padding the set with pieces that do not compare.

Then the piece's views divided by that baseline:

- Below 0.7x: weak.
- 0.7x to 1.5x: normal.
- 1.5x to 3x: strong.
- Above 3x: an outlier.

These are decision thresholds, not laws of physics. They exist so "it did okay" turns into something you can act on. Because the ledger keeps every reading, your baseline gets more honest every week instead of resetting each time we talk.

## Step 3: diagnose the shape

For anything outside the normal band, I match the shape of the numbers to one of these, name which one I applied, and say why.

- **Strong reach, weak watch time.** The opening attracted them, the body wandered. Next: shorten the setup, move the evidence earlier.
- **Weak reach, strong watch time.** The substance worked, the packaging did not. Next: test a new hook and a new first frame on the same idea.
- **High views, few follows.** The topic may be too broad to make anyone feel identified. Next: strengthen identity and positioning.
- **Strong saves, weak shares.** Useful, but not emotionally expressive. Next: add stakes or social relevance.
- **Strong shares, weak business response.** Excellent discovery content. Next: publish an authority sequel that goes deeper.
- **Modest reach, strong enquiries.** Narrow but commercially valuable. Next: continue the series.
- **Strong across every metric.** An emerging franchise. Next: see Step 4.

If the shape does not cleanly match any row, I say that plainly instead of forcing a fit. If a diagnosis needs a number nobody has, I name the missing number rather than guessing which row applies.

## Step 4: winners earn sequels

A piece qualifies as a winner when it beats about **3x** your own baseline, **or** when it produces unusually strong business signals even without the reach. That "or" matters. A bookkeeping firm owner's piece that reached four hundred people and brought two enquiries is a winner, and treating it as a flop because it did not go wide is how people quit their best work.

Every winner gets a **franchise card**, one file per franchise, in `content-os/library/franchises/`, named `YYYY-MM-DD - franchise-name.md`. It is a card, not a paragraph buried in a script file, because a franchise outlives the piece that started it.

```
# Franchise: {the name, in your words}

Started: YYYY-MM-DD
Content job: (reach / authority / trust / business)
Status: open

## The original piece
- Link:
- Posted: YYYY-MM-DD
- Format:

## Core thesis
{the idea underneath it, one or two sentences, in your words}

## The mechanism that won
{the reusable shape, never the wording. Also filed as a Library Entry in
content-os/library/ marked as your own results, which is the highest rung of
evidence you have.}

## Performance
- Multiple: Nx vs a baseline of N from N comparable pieces (as of YYYY-MM-DD)
- Whichever quality numbers were strong:
- Business signal, if any:

## Why it probably worked
{topic, hook, format, emotion, proof, or timing. Say which, and why.}

## What people actually said
{real comments and questions, in the exact words people used. Never invented.
This is the raw material for the sequels.}

## The three sequels this owes you
| # | Type | Idea card | Posted | Result |
|---|---|---|---|---|
| 1 | Direct sequel |  |  |  |
| 2 | Different format |  |  |  |
| 3 | Deeper authority version |  |  |  |

## Running total
{the original plus every sequel that has actually shipped, updated as they land}
```

Then I log **three sequel obligations**, not three finished pieces:

1. One direct sequel, the next chapter of the same argument.
2. One version in a different format.
3. One deeper authority version.

Angles worth pulling from: the story behind the claim, the detailed framework, a case study, the strongest objection, the common mistake, the beginner version, the advanced version, the failure version, a demonstration, or a direct answer to the loudest comment. If the comments hand you a stronger angle than any of these, take the comments.

Each obligation gets filed as an Idea Card in `content-os/ideas/`, with the angle left blank as always, so it enters the normal flow and still has to earn its place. I do not write the sequels here.

I fill in a sequel's result on the card only when that piece has actually run. Never in advance.

If a franchise card already exists for this thesis, the new piece gets logged as a result on that card instead of starting a second one.

## Step 5: lessons become rules

At the end I list what this week taught us, in plain sentences. You confirm or reject each one.

Every confirmed lesson gets appended to `MY-RULES.md` with the date and the piece that revealed it. Rejected ones get dropped, not argued.

That file is the memory of this whole system. It is why the hooks I write in month three fit you better than the ones I wrote in week one (see laws.md: corrections become written rules).

Example entries from a career coach's file after four weeks:

- "My audience does not respond to salary numbers. They respond to the moment someone got passed over. (2026-08-19, from the piece about the promotion.)"
- "Never open with a question. It reads as a survey. (2026-08-12.)"

## Step 6: the weekly verdict

I finish with five short lines, and nothing longer:

1. **What worked, and the job it was working for.** One sentence with the multiple in it.
2. **What did not, and which diagnosis row explains it.**
3. **What your own results have now proven**, if this week added anything to that. Your own proof outranks every competitor entry in your library (see laws.md: evidence hierarchy).
4. **What the patterns picture is showing**, with its own honesty attached. Early on this reads "still collecting evidence", and that is the correct answer, not a failure.
5. **What gets made next**, as a list of idea cards already sitting in `content-os/ideas/`, including this week's sequel obligations.

If the week produced nothing conclusive, the verdict says so in one line. A quiet week is a real result. Manufacturing a lesson from three data points is how people end up with a rulebook full of superstitions.

## What I never do here

- Never estimate a number you did not give me.
- Never call something a winner without real data behind it.
- Never write a rule you did not confirm.
- Never grade a piece against a job it was not built for.
- Never rewrite an old ledger entry to make a story tidier.
- Never claim the patterns picture is confident when it says it is not.

## Next

Your sequels are now Idea Cards sitting in `content-os/ideas/`, alongside everything else you captured this week. Say **"score my ideas"** and we go back to **M3 Qualify** (`03-qualify.md`) to decide what gets made next.
