# The Testing Program: how to run headline tests that compound

Read this before giving any Mode B verdict. These are the working rules of a testing program,
not one-off test math. The goal is never "which of these two lines is better" - it is "what does
this market keep telling us, test after test."

## Rule 1: Test the headline first (but respect upstream)

The headline is 80 cents of your dollar. Before testing button colors, page length, images, or
form fields, exhaust the headline. A headline change routinely moves opt-in rate by 30-100%;
everything else on the page fights for scraps. One exception outranks it: if paid ads drive the
traffic and the AD's angle is still unproven, test the ad angle first - changes made upstream in
the funnel touch every visitor who follows behind them, so they carry the biggest possible
swing. Order of leverage: ad angle → page headline and lead → everything downstream.

## Rule 2: Write the hypothesis down before you test

Before changing anything, lock the current version in as the control and write one sentence: why
you believe the current result is what it is, and what the change should therefore do. If you
cannot state a concrete, falsifiable reason, you are not ready to test. And when you run out of
hypotheses, do not invent one from taste - go back to customer language, avatar research, and
whatever angle is winning in live ad data. A hypothesis grounded in the market's own words beats
one grounded in what sounds clever.

## Rule 3: One variable at a time, duplicate not edit

If the two arms differ in headline AND image AND button text, the test teaches you nothing - 
you cannot know what caused the gap. Two arms, one difference. Build the challenger as a
duplicate of the live page rather than editing the original, so the control stays untouched
while the test runs. This split-run discipline is a century old - the early direct-response
masters tracked every reply with coded coupons - and it has not changed: isolate, then measure.

## Rule 4: Big swings before tweaks

Test hierarchy, in order of how much a win teaches you:

1. **Angle / claim form** - problem-led vs result-led vs mechanism-led vs identity-led. A win
   here re-aims the whole page.
2. **Awareness level** - who the headline assumes is reading. Wins here reveal who is actually
   clicking.
3. **The specific promise** - which outcome, which number, which timeframe.
4. **Wording** - phrasing, rhythm, word swaps. Only worth testing once 1-3 are settled.

A wording tweak that wins by 8% is noise. An angle change that wins by 40% is a map of your
market. When a page is stuck under its target rate, the answer is almost never a tweak.

## Rule 5: The 15% rule (calling a winner)

Opt-in pages live on small conversion counts, so tiny gaps are noise. Working rule:

- **Relative lift > 15%** → call the winner, retire the loser, log it.
- **Under 15%** → no winner. Keep the control, kill the variation anyway (it failed to beat the
  champion meaningfully), and make the next test a bigger swing.
- Relative lift = (winner rate − loser rate) ÷ loser rate. The skill computes this; never make
  the member do math.

## Rule 6: Sample sanity

- Under **~30 opt-ins per arm**: directional only. Say it plainly. You may still act on it when
  the lift is large and traffic is slow - waiting three more weeks for statistical purity costs
  more than an occasional wrong call on a free-to-change headline.
- Under **~10 opt-ins per arm**: no verdict at all. Keep running.
- Views matter less than conversions. 10,000 views with 12 opt-ins is a weaker read than 2,000
  views with 45.

## Rule 7: The control keeps its crown, and only numbers vote

The reigning headline is only ever dethroned by real numbers, never by a prettier rewrite, a
higher rubric score, or anyone's gut feel - including yours. Rubric scores explain results and
generate challengers; the market decides. Opinions ("this one sounds better") are not data, and
treating them as data is how good tests get killed early and bad ones kept alive. When the
blended number is ambiguous, break it down by traffic source or segment before ruling. When a
new control is crowned, the old one goes in the ledger with what its loss taught you.

## Rule 8: After the verdict: close means iterate, way-off means rebuild

Sort every test outcome into one of two buckets. **Close** - the challenger produced real
results but not a win: keep the format, write a fresh hypothesis, iterate. **Way off** - 
meaningful traffic, near-zero conversions: stop patching. Rebuild the headline from a genuinely
different angle instead of nursing something that fundamentally is not working.

## Rule 9: Log every test, read the ledger before every verdict

An unlogged test is a lesson you paid for and threw away. The ledger
(`headline-tests/<page>.md`) is the member's private swipe file of what THEIR market responds
to - more valuable than any guru's swipe file, because it is evidence about their exact buyers.
Before any new verdict or rewrite, read the whole ledger and update the "What this market keeps
telling us" notes. Trend beats anecdote:

- Same angle wins twice → that awareness/sophistication read is confirmed; push further in.
- Mechanism arms keep beating bare claims → the market is Stage 3-4; name and brand the mechanism.
- Identity arms win → sophistication is topping out; sell to who they are, not what they get.
- A long-reigning control slowly fading with nothing else changed → novelty decay. Headlines
  that won partly by standing out lose power as competitors copy the pattern. The fix is a
  genuinely fresh angle (steal shapes from unrelated markets), not a reword of the tired one.

## Rule 10: When to stop testing a page

Stop when a page holds a rate that makes the funnel's economics work (cost per lead where the
back-end math is profitable) AND two consecutive big-swing challengers have failed to beat the
control. Then the next lever is the traffic or the offer, not the headline. Testing past that
point is procrastination dressed as optimization. And the hard version of this rule: if several
genuinely different angles have ALL failed to move the needle, the words were never the
problem - question the offer itself. No headline fixes a promise the market does not want.

## Cross-signal diagnostics (when the numbers disagree with each other)

Read these BEFORE blaming the headline. The gap between two metrics is often the real finding.

- **High click-through, low opt-in** → the promise that earned the click is not being kept on
  the page. This is a broken handoff, not bad traffic - do not broaden or kill the audience.
  First check the page headline against the winning ad: same promise, same tone, same angle?
- **The fix direction:** rewrite the PAGE to match the proven ad, not the other way round. The
  ad already demonstrated what the market responds to; the page follows the winner. Better
  still, derive one from the other - build the page headline word-for-word from the winning
  ad's promise (or the ad from the page's proven benefit line) so congruence is automatic.
- **A suspiciously great number** (click-through or open rate far above baseline) → audit it
  before celebrating. Eye-catching creative can pull curiosity clicks from people who were
  never buyers; the "win" upstream is often the first symptom of a crater downstream.
- **A page that stopped converting with no test running** → check for a systemic cause first
  (traffic source changed, offer aged, market moved up the sophistication arc) before
  concluding the headline broke.
- **Mismatch inside the page** → the handoff can also break between the page's own sections.
  Read the page top to bottom: does every section keep the promise the headline made, or does
  one quietly contradict it?

## Cost per lead is the tie-breaker

Opt-in rate is the page's score; cost per lead is the business's score. When two arms are close
on rate, the one feeding cheaper leads wins. And when the rate is fine but CPL is high, the
problem lives upstream in the ad or the audience - say so instead of squeezing the headline.
