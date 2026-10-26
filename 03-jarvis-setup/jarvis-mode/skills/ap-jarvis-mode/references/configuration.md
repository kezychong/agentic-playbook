# JARVIS member configuration

This is the agent-facing contract for schema 1. It describes the member's existing
Hermes profile and source files. It does not replace the member's chief-of-staff
persona, authentication, chats, profile files, or operating rules. Setup adds JARVIS
guidance beside that existing profile.

## What the agent discovers

The agent must discover and confirm the member's existing main-device destination,
headless-device destination, profile ID, timezone, and real source locations. A folder
name is not profile proof: the headless destination is accepted only when Hermes'
`profile_matches_home(profile_id, profile_root)` matcher returns true. The agent must
also run package preflight before importing packaged code.

The member chooses visible boxes. The installer has this exact mapping:

| Visible box | Source adapter(s) |
| --- | --- |
| `agent_helpers` | `agent_helpers` |
| `waiting_on_you` | `agent_state` |
| `agent_in_flight` | `agent_state` |
| `overnight_jobs` | `overnight_jobs` |
| `next_meeting` | `next_meeting` |
| `today` | `today_plan`, `lever` |
| `spend` | `spend` |
| `scoreboard` | `one_thing_scoreboard` |
| `fleet` | host data; no backend source ID |

`waiting_on_you` and `agent_in_flight` stay separate choices even though they read
the same state file. `NOW` and voice controls remain available. `brains`, `scoreboard`,
and `log` are additional backend source adapters; enable them when the member has
real paths for them.

When a selected source cannot be found, the agent asks the member for its real path.
It records the source only after the member confirms it. It never invents a path,
copies another person's source, or creates an automatic connector. Missing, stale,
unreadable, or unconfigured sources stay visible with an honest status such as
`missing`, `stale`, `unreachable`, or `unconfigured`.

## Source adapters and original formats

Adapters read the member's existing files or database in place. They do not rewrite
those sources, convert them, or silently change their format.

| Source ID | Input and read format |
| --- | --- |
| `agent_state` | Markdown `STATE.md`. Rows under `## In flight` use `- [id] where | next: action | owner | follow_up_at | last update`. `## Recently closed` rows are counted. Optional `briefs_path` is Markdown headings like `## [id] Title` with `- what:`, `- why:`, `- do:`, `- takes:`, `- where:`, or `- updated:` bullets. |
| `agent_helpers` | Read-only SQLite `state.db`, table `async_delegations`. The adapter reports recent and running delegations, delivery state, goals, and summaries. |
| `next_meeting` | A member-provided Google service-account JSON path, used by the packaged helper with Calendar read-only scope. `hours` is 1–168; `python_path` is optional. The package contains no credential. |
| `today_plan` | Markdown with flat front matter such as `date`, `build_task`, `build_status`, `build_next_action`, `content_*`, and `momentum_*`, plus a `## Today` heading. The first body sentence is the headline. |
| `overnight_jobs` | JSON object with a `jobs` list, or a bare list. Jobs use fields such as `enabled`, `state`, `last_run_at`, `last_status`, `last_error`, `next_run_at`, `id`, and `name`. |
| `one_thing_scoreboard` | Markdown front matter for `build_streak`, `content_streak`, `best_build_streak`, and `lessons_shipped_since_start`, plus dated bullets such as `- 2026-01-02 · build ✅ · content ❌ · note`. |
| `spend` | Read-only SQLite `state.db`, table `session_model_usage`. Unknown or zero cost stays `null`; the adapter never estimates a dollar value. |
| `lever` | Markdown front matter key `pm_current_one_lever`, or the first content line under `## Current ONE Lever`. |
| `brains` | A list of configured mirror directories. The adapter reports each directory and its newest-file timestamp; it does not manufacture brain content. |
| `scoreboard` | Markdown whose first heading or non-empty line is the headline; the next two non-heading lines are the detail lines. |
| `log` | Append-only Markdown; the adapter returns the newest dated bullet beginning `- 20…`. |

Source paths must be absolute and must not contain `..`. The example uses the neutral
`/absolute/member/...` prefix so it contains no real user name, IP, or credential.
The calendar entry is a path to a member-owned credential file, not credential data;
the member keeps that file outside the package.

## Exact setup handoff

The agent passes the member's choices to the existing `scripts/install.py --setup`
entrypoint. The script validates the prospective document through the packaged
`config.py` validator and writes only the selected headless profile's
`jarvis/config.json`. It writes atomically with directory mode `0700` and file mode
`0600`. The default is a dry run; `--apply` is the explicit write step after
preflight, profile proof, and the required host checks pass.

Each selected box is repeated as an `--enabled-box` argument. The installer resolves
its required source IDs through the mapping above. `--enabled-source` can add source
adapters such as `brains`, `scoreboard`, or `log`; `--sources-json` supplies the
member-confirmed paths, and `--brains-json` supplies the mirror list. The setup
entrypoint does not SSH, restart services, enable a guessed plugin, or obtain OAuth.

Before either command, the agent transfers the package over the member's existing
trusted SSH route, verifies the package SHA-256 on both devices, and runs full package
preflight on both. That transfer and verification belong to the agent workflow; this
installer does not SSH, transfer files, or restart services.

On the main Mac, run the setup command against the actual Desktop Hermes home. This
is the main-device destination, not a guessed profile directory:

```sh
python3 scripts/install.py /absolute/member/ap-jarvis-mode \
  --setup \
  --main-destination /absolute/member/main-mac/Desktop-HERMES_HOME
```

On the headless Mac, run a separate command against the member-selected Hermes
profile root. This is where the profile proof and schema-1 configuration are applied:

```sh
python3 scripts/install.py /absolute/member/ap-jarvis-mode \
  --setup \
  --headless-destination /absolute/member/headless-mac/Hermes-profile \
  --profile-id member-profile \
  --agent-name chief-of-staff \
  --owner-label Member \
  --timezone Etc/UTC \
  --enabled-box agent_helpers \
  --enabled-box waiting_on_you \
  --enabled-box agent_in_flight \
  --enabled-box overnight_jobs \
  --enabled-box next_meeting \
  --enabled-box today \
  --enabled-box spend \
  --enabled-box scoreboard \
  --enabled-box fleet \
  --enabled-source brains \
  --enabled-source scoreboard \
  --enabled-source log \
  --sources-json '{"agent_state":{"path":"/absolute/member/agent/STATE.md","briefs_path":"/absolute/member/agent/WAITING-ON-OWNER.md"},"agent_helpers":{"path":"/absolute/member/hermes/state.db"},"next_meeting":{"service_account_path":"/absolute/member/calendar/service-account.json","python_path":"/absolute/member/bin/python3","hours":36},"today_plan":{"path":"/absolute/member/plans/TODAY.md"},"overnight_jobs":{"path":"/absolute/member/agent/cron.json"},"one_thing_scoreboard":{"path":"/absolute/member/plans/SCOREBOARD.md"},"spend":{"path":"/absolute/member/hermes/state.db"},"lever":{"path":"/absolute/member/plans/LEVER.md"},"scoreboard":{"path":"/absolute/member/agent/SCOREBOARD.md"},"log":{"path":"/absolute/member/agent/LOG.md"}}' \
  --brains-json '[{"id":"member-brain","label":"Personal brain","path":"/absolute/member/brains/personal"},{"id":"company-brain","label":"Company brain","path":"/absolute/member/brains/company"}]'
```

Replace every `/absolute/member/...` destination and source path with a path
discovered on this member's devices, and replace `Etc/UTC` with the member's
discovered IANA timezone before applying. Run each command without `--apply` first.
Add `--apply` only after the dry-run report confirms the selected profile and all
requested inputs. A local receipt or schema check is installation evidence; live
completion still requires the authenticated profile response and the member smoke
checks described in `SKILL.md`.

## Calendar runtime dependency

When the calendar box is selected, its configured interpreter must provide
`google.oauth2.service_account` and `googleapiclient.discovery` (the
`google-auth` and `google-api-python-client` distributions). Reuse a verified
member-owned environment or prepare a dedicated environment and set
`sources.next_meeting.python_path` to its interpreter. Do not change the
member's main Hermes environment merely to satisfy this optional reader.
The current reader uses the member's Google service-account access; an existing
OAuth connection alone is not proof that this reader is configured. Missing
permission or credentials must be reported, never replaced with sample events.
