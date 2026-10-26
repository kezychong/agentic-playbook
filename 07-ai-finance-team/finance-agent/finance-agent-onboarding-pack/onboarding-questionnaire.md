## Finance scope — by Kezy

Blank Finance Agent template; no live profile or connection is included. Work in manual mode
with owner-supplied exports first. This edition permits analysis and drafts only: no account
connection during setup of this package, payments, trades, filings, payroll execution,
production ledger writes, invoice edits or period locks. The go-live checklist approves only
read-only reporting readiness; it never unlocks writes. Amount thresholds prioritize review,
not permission to spend. Obtain separate approval before any future read-only connection,
profile installation or schedule. Missing data stays unknown; a missing field is not zero.


# Onboarding Questionnaire

Fill this in before you connect anything. Your answers become the settings your agent uses every
single time it touches money.

Keep this file. Never write a password, a login, or a connection key into it. Those never belong
in a document, and your agent never asks you for one in chat.

## Who this is for
- A business owner filling in facts about their own business. No technical answer required.
- Every question below is about your business, not about your computer.
- Unsure on one? Write "not sure" and move on. Your agent will help you settle it later.

## Question 1 - Which accounting software do you use?
This is the most important answer in the pack. It decides your whole setup route.

> Xero / QuickBooks / Neither, I keep no accounting software

Pick "Neither" honestly if your books live in a spreadsheet, in a folder of statements, or in
your head. Manual mode is fully supported and runs the same close and the same reports. You just
hand over statements once a month instead of the agent fetching them.

What happens next, based on your answer:
| Your answer | Your next file |
|---|---|
| Xero | connect-xero.md |
| QuickBooks | connect-quickbooks.md |
| Neither | skip straight to money-safety-agreement.md |

## Section A - Your business
A1. Business name, exactly as it appears on your invoices:
> _______________________________________________

A2. Your name, as the person who approves money decisions:
> _______________________________________________

A3. Do you run more than one business or legal entity?
> No / Yes, and here they are: ____________________

If yes, list them. Your agent will never mix two sets of books, and it will ask which one you
mean every time an ask is unclear.

A4. What you sell, in one line:
> _______________________________________________

## Section B - Your money settings
B1. Currency you report in:
> _______________________________________________

Write the three-letter code you see in your bank, for example USD, GBP, EUR or AUD. If you get
paid in more than one currency, write the one your accounts are reported in.

B2. Approval threshold. Any expense at or above this amount needs your explicit yes before your
agent acts on it in any way.
> Suggested starting point: 100 in your currency
> Your number: ____________

Why 100. Low enough that nothing meaningful slips past you, high enough that you are not
approving coffee. Raise it once you trust the agent. Lower it any time, instantly, by telling
your agent the new number.

Below the threshold the agent still reports every expense. It just does not stop and ask.

B3. Invoice terms. How long do clients have to pay you from the invoice date?
> Net 7 / Net 14 / Net 30 / Other: ____________

"Net 30" means payment is due 30 days after the invoice date. This is how your agent works out
what counts as overdue, and how many days overdue it is.

B4. Financial year end. The date your books close for the year.
> Day and month: ____________

If you are unsure, it is on last year's accounts, or your accountant knows it in five seconds.

B5. Week start day. Your weekly money report runs from this day.
> Monday / Sunday / Other: ____________

## Section C - Your current bookkeeping reality
Answer these honestly. The agent works better knowing the mess than guessing there is none.

C1. Are your bank accounts and cards connected to your accounting software?
> All of them / Some of them / None / Not applicable, manual mode

C2. When did you last reconcile, meaning match every bank line to a record in your books?
> This month / A few months ago / Never / Not sure

C3. Roughly how many sales invoices do you issue in a month?
> ____________

C4. Do you have any invoices currently overdue?
> No / Yes, roughly how many: ____________

C5. Where do your supplier bills and receipts live?
> In the software / In an inbox / In a folder / Scattered

## Section D - Your first month
D1. Which month do you want the agent to close first?
> ____________

Pick a month that has already ended. Closing a month still in progress is guesswork.

D2. Do you want the weekly money report turned on?
> Yes / Not yet

D3. Do you want the monthly close reminder turned on?
> Yes / Not yet

Recurrence honesty: if you answer yes, these run every week and every month from then on, on
their own, until you tell your agent to stop. Nothing runs until you approve the schedule.

## Section E - Acknowledgements
Initial each line:
> ____ My agent never moves money, never pays anyone, and never files anything with a government
>      office. Not now, not after go-live, not ever.
> ____ My agent drafts invoice emails and overdue chasers. I am the one who sends them.
> ____ I set the approval threshold and I own every approval above it.
> ____ My agent starts read-only and only writes after the go-live checklist passes.
> ____ I will read and sign money-safety-agreement.md before anything goes live.

## Hand this to your agent
When this sheet is filled in, open the Claude app or the Codex app and say:

> "Here is my filled finance questionnaire. Set up my finance agent from it, tell me back every
> setting you saved, and stop before connecting anything."

Easiest way: paste this whole file into the chat and answer the questions right there. Your agent
writes the answers down.

Your agent turns your answers into its permanent settings. It reads back what it saved so you
can catch a wrong number before it matters.

For your agent, these are the settings filled from your answers:
| Setting | Filled from |
|---|---|
| {{BUSINESS_NAME}} | A1 |
| {{OWNER_NAME}} | A2 |
| {{ACCOUNTING_SOFTWARE}} | Question 1 |
| {{CURRENCY}} | B1 |
| {{APPROVAL_THRESHOLD}} | B2 |
| {{INVOICE_TERMS}} | B3 |
| {{FINANCIAL_YEAR_END}} | B4 |
| {{WEEK_START_DAY}} | B5 |

Now open the file your Question 1 answer pointed you to.
