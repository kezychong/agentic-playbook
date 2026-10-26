# Connect Xero — optional, approval required

Agentic Playbook — **by Kezy**

This adapts the supplied Xero connection walkthrough. No connection is included or tested.
Use manual exports for the first rehearsal. Connector availability, regions, prices and scopes
must be checked in current official provider and host documentation at use-time; this pack does
not promise a particular listing or geographic rollout. For QuickBooks Desktop or an unsupported
account, use exports rather than assuming an Online connector can read it.

## Before starting
Complete the questionnaire and money-safety agreement first. Confirm the exact organisation, owner,
currency, permitted records, reporting dates and whether you hold appropriate access. Do not
request broader administrator access simply because a connector asks for it. Decide who may
approve access and where sanitized reports will be stored. Host/model/API fees may apply.

## What a connection does
A connector allows the host to fetch authorized accounting records. The provider issues tokens;
the host or connector may store them, and permitted records may be sent to the model provider.
Read the publisher's storage, retention and revocation terms. Keep tokens in approved secure
local setup, never chat, source files or reports. The Playbook contains no credential service.

## Route A — a supported host connector
1. Open the host's connector settings and look for Xero. Confirm its publisher from the
   provider's official documentation, not just a similar display name.
2. Review requested scopes, company access, data flow and cost. Request only necessary read
   access. If a connector grants writes that cannot be disabled, prefer manual exports; a
   prompt-level read-only instruction is not a security lock.
3. Show the exact proposed connection and ask the owner to approve. The owner signs in on the
   provider's verified authentication page. Check the full hostname and official sign-in flow;
   a lookalike domain containing `xero.com` is not sufficient. Never ask for the password in chat.
4. Choose exactly one organisation. Review the consent screen and approve only the agreed scopes.
5. Verify the connection with the checks below; do not treat a successful login as proof.

## Route B — no supported listing
Do not automatically install a server or assume a source repository exists. Ask the agent:

> “Find the current official Xero integration documentation available in my host. Show
> publisher, prerequisites, scopes, token storage, data flow, costs and removal steps. Prepare
> a setup plan only. Do not install, connect or modify a profile without my approval.”

If support cannot be verified, use manual mode: dated statements, invoice records including
credit notes, bills and a ledger/P&L export. The reporting and reconciliation methods stay the same.

## Prove read access
Ask “Which organisation can you see, and what is the source?” Match the exact name yourself.
Then request the three most recent invoices: number, client, amount, status and date. Compare
all five fields against the source. Stop if any differs. For an invoice marked paid, require
its full record, credit-note check and a matched bank deposit; status alone is not cash proof.
The first lookup should be small. Record dates, scope and gaps without copying raw credentials.

## Expiry, revocation and removal
On expiry or error, stop fetching and report lost coverage. Never fill missing numbers by guess.
To revoke, remove the connected app in Xero's account settings, remove/disable it in the
host and securely remove stored tokens according to its instructions. Verify that a new read
fails; revocation does not erase previously exported copies. Review retained exports separately.
A written agreement does not guarantee immediate technical revocation; check provider behavior.

## Next
Run [the readiness checklist](go-live-checklist.md). Passing enables only trusted draft reporting,
never invoice writes, payments, trades, payroll, filings or schedules.
