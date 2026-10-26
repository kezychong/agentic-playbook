# Connections: access, cost and data flow

Agentic Playbook — by Kezy

Start with local fictional files. A connector is an optional route to source data, not a requirement
for learning the workflows. Before any live connection, prepare this review:

| Decision | Record before approval |
|---|---|
| Purpose | Exact task and records needed |
| Publisher | Official provider and verified host support |
| Scope | Account/entity, read permissions, excluded write tools |
| Data flow | Service → connector/host → model provider → local draft |
| Secrets | Approved secure token store; never chat or report |
| Retention | What each service stores and how to remove copies |
| Cost | Existing subscription, API/model charges and budget; unknown stays unknown |
| Revocation | Provider connected-app removal, host disablement and token cleanup |
| Proof | One small read checked against the original record |

Show the owner this plan before installation or consent. The owner signs in using the provider's
verified flow. Prefer read-only scopes and short-lived access. When write scope cannot be excluded,
explain that prompt rules are not technical access controls; prefer manual exports.
Never infer account access from an example or a blank settings file.

Meeting and call workflows need only expressly allowed calendars, chats or recordings. They do
not gain permission to send or book. Sales pages stay local until approved for publication.
Finance uses its [specific connection guides](../07-ai-finance-team/workflow.md) and forbids live
financial writes. If a tool fails, disclose incomplete coverage instead of inventing data.

To revoke: remove the connection in the provider, disable it in the host, remove stored tokens
securely, and verify a fresh read is denied. Separately decide what to do with retained exports.
No connection was created or verified here.
