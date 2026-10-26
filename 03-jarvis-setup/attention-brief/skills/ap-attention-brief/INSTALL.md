> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

---
stage: shipped
---
# Attention Brief: Install & Use

Collection: Agentic Playbook — by Kezy. Use the included canonical skill folder.

Your agent brings you the few things needing attention each morning.
Each evening, it records what finished, what is stuck, and what you parked.
It checks your chosen sources during each run and keeps one shared list.
You get evidence beside each action, with one reminder at most after an unanswered evening close.

Works in Claude Code and in Codex.

## What you need first

- Your usual agent app and this zip.
- A computer that can stay awake for the chosen times.
- Access to the calendar and any inbox or chats you want checked.

Your agent installs its own requirements.
It asks you to connect an account only when your login is needed.

## Install

Give the zip to your agent and say:

> Install this attention brief, ask for my settings, and switch on my morning and evening routine.

Your agent asks one question at a time.
It reuses any goals setup you already have.
It writes your settings, the shared list, and the automatic routine.
Default times are 08:00 and 21:00 in your timezone.
You can choose different times.

The routine uses a small wrapper, like a bridge from your computer's alarm clock to your agent.
Your agent writes that bridge and the scheduler entry itself.
A scheduler is the computer's alarm clock for tasks.
On macOS, your agent uses a LaunchAgent.
On Linux, it uses cron.
On Windows, it uses Task Scheduler.
Your agent selects the matching route; you do not choose or configure these tools.

It also sets one conditional reminder for an unanswered evening close.
All three triggers share your list and reply record.
It shows the saved paths and the exact pause action.

## Check it worked

Your agent fires the installed routine once and shows its real output.
Each action includes a source and checked time.
It shows the job identifier, saved note, run result, and next scheduled times.
If there is nothing to report, it shows the successful check record.
It labels anything untested "assumed, not checked".
A failed test leaves the routine paused.

## How to use it

1. Read the morning brief when something needs you.
2. Choose today's main task if it is missing.
3. Reply to the evening close with done and proof, stuck and why, or park until a date.
4. Agree tomorrow's main task when asked.
5. Say "Pause my attention brief" whenever you want all its triggers stopped.
6. Say "Change my attention brief" to update times, sources, or delivery.
7. Say 'Run my morning brief once right now' to fire it on demand.
8. Say 'Uninstall my attention brief' to remove the routine and its files.

Your agent saves these changes and checks them on the next run.
With file delivery, reply in the daily note or tell your agent in your usual app.
The agent records your reply in the shared record.

## What it will NOT do

- Send messages to anyone else.
- Read accounts you did not allow.
- Claim something finished without checked proof.
- Treat a failed source check as an empty inbox.
- Send more than one reminder after an unanswered close.
- Do your main task inside the morning brief.

## Hermes addendum

Tell your Hermes agent the same installation sentence.
It uses Hermes cron jobs for the morning and evening prompts instead of the computer's wrapper route.
It also schedules the same conditional reminder check.
It checks that the background service is running and the timezone is correct.
Each prompt names the shared settings and files because scheduled sessions start without your chat history.
It reuses a matching existing morning job to avoid duplicate briefs.
It test-fires one installed job, shows the result, and records every job identifier.
Say "Pause my attention brief" to pause all its jobs.

Hand this block to your agent: inspect the installed scheduling tools before writing jobs.
Use native job creation, listing, manual execution, and pause controls supported by that installation.
Do not invent configuration keys or create recursive jobs during scheduled runs.
Keep reminder attempts in the shared record because a scheduled session cannot depend on an earlier chat.
