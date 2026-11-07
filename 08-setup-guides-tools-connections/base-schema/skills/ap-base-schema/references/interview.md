# The interview

Run these phases in order. **One question at a time. Wait for the answer.** Do not batch
questions into a list, and do not move on until the exit condition is met. Restate what you
heard in their own words at the end of each phase and get a yes.

⛔ **Do not propose a single table until Phase 6 is done.** They will push you to start
designing early. Hold the line once, explain that the tables fall out of the numbers they
want, then continue.

## Phase 0 — Orientation
- What does the business do, in the words you'd use with a friend?
- Walk me through a normal week.
- Where does the information live right now — which chats, which spreadsheets, whose head?
- Where does each kind of record get its number — here, or from another system (the bank,
  the accounting software, a regulator)? (Feeds the Record Home Map after Phase 5.)

Exit: you can state the business in one sentence and the pain in one sentence.

## Phase 1 — Find the spine
- While drafting, use only fictional or fully minimized examples and a rounded volume band.
- Finish this: in a typical year we do tens, hundreds, or thousands of these.
- Point at a fictional or fully minimized one — when did it start, when did it finish?
- Does money come in per one of these? Does more than one person touch one?

Common spines: project, job, case, engagement, order, booking, event, shipment, patient
episode, cohort, campaign, listing, retainer month, production batch.

Two failure modes: if their candidate is something one person finishes in an hour, it's a
**task** — go up a level. If it's a company they've worked with for years, it's a **client** —
go down a level. For a retainer, name the fork: the spine is either the retainer relationship
(with monthly invoice rows under it) or the retainer month itself — pick by whether scope
changes month to month.

Exit: a named unit, a plural noun, a rough annual volume band, one fictional or fully minimized
example named aloud. Do not put personal/client details or live figures in chat, fixtures, or
source control.

## Phase 2 — Lifecycle
- From first contact to money in the bank, what states does one pass through?
- Who moves it from each state to the next? What has to be true before it can move?

Exit: an ordered list of 4–8 stages, each with its trigger. Fewer than 4 = they're
compressing. More than 8 = some are tasks, not stages.

## Phase 3 — Money in
- How do you charge — one price up front, milestones, retainer, per unit, subscription?
- Do you quote before you invoice? Does the quote need approval or a PO?
- Is there tax, at what rate? Which currencies? When do you invoice vs when does money arrive?

Exit: you can draw the revenue-document chain (e.g. enquiry → quotation → PO → invoice →
payment) and you know whether they run the business on **cash or accrual**.

## Phase 4 — Money out
- For one of these, who do you pay — freelancers, suppliers, ad platforms, nobody?
- Do you need profit on a single one, or only for the month? Pay in a different currency?

A genuine fork: many businesses (coaching, consulting, software) have no per-unit variable
cost worth tracking. If so, say plainly you're **not** building a cost table and gross profit
per unit isn't a question this base will answer, then move on.

Exit: the shape of the cost side, or an explicit decision not to build one.

## Phase 5 — People and parties
- Who inside the business touches one, and in what roles? Do you need to see who's overloaded?
- Who outside is involved — do you bill them, pay them, or both?
- Do you collect anything at onboarding (bank details, tax numbers, registration docs)?

Exit: which counterparty and people tables are needed, and roughly what each carries.

## After Phase 5 — The Record Home Map
Load `references/record-home-map.md`. Walk each kind of record named so far, one at a time:
- Where does its number come from? (That's its home.) When it has to change, where is the
  change made, and by whom?
- Born here, Copy, Request, Frozen figure, or Not kept here?
- For a Copy: does the home have a box that can carry our code (the match key)? Who notices
  when copies stop arriving? How would copies get here — by hand from an export, or "not
  known yet"? (⛔ Never pick or promise a connector.)
- Is any of it personal data or client money? Then what's the least we can keep?

Exit: one line per kind of record in `templates/record-home-map.md`, unknowns as
`⬜ ASK OWNER: …`, and a yes to the restated map. Freshness waits for Phase 6.

## Phase 6 — The weekly number
- What number do you want to see on Monday morning?
- What question about the business takes you more than ten minutes to answer today?
- Last time a number surprised you, what was it? At month end, what does your accountant
  assemble by hand?

Exit: **3–6 named metrics.** Write each down — this list is the **acceptance test** for the
entire design. Any table or field that doesn't feed one of these metrics or a Phase-7 proof
must justify itself under R13. Then, for every Copy line in the Record Home Map, ask how old
the copy may be when this number is read, and write it as that line's freshness.

## Phase 7 — Proof and paperwork
- If a client disputes an invoice a year from now, what do you pull up?
- If the tax office asks, what must you show? What do you currently screenshot and send?

Exit: the attachment/document list, each placed on the row where that document is produced.

# Design, then challenge

After Phase 7, present the blueprint (format in [blueprint-and-build.md](blueprint-and-build.md)).
Then run two mandatory checks before anything is built:

**Walk two fictional or fully minimized jobs through it while drafting.** Use one unit that
went smoothly and one that went wrong (scope creep, late payment, dispute, cancellation).
Walk each row by row, out loud. Anything they can't record = a missing field. Anything they'd
never look at = a field to delete. The one that went wrong is worth more than the one that
went well. A separately approved local acceptance step may repeat this with real records and
details; keep them local and never put them in chat, fixtures, or source control.

**Run the kill list.** Field by field: who reads this, and when? Cut anything without an
answer. Expect to remove 15–30% of the first draft. That is normal and is the point.
