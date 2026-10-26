#!/usr/bin/env python3
"""
calendar_data.py - the Calendar tab: what went out behind you, what you have
planned ahead of you.

Standard library only. No network calls in this file.

Behind you: read from content-os/posted.md, the append-only record of what
was actually published. Never written to from here.

Ahead of you: content-os/calendar-plan.json, a tiny store the cockpit owns
outright. One writer, atomic writes, every change receipted.

An empty posted record is the normal state of a new workspace and shows as an
empty past, never as an error.
"""

import datetime
import re
import secrets
import threading

import posted_ledger
import workspace as ws

PLAN_FIELDS = {"date", "title", "note", "status"}
_PLAN_LOCK = threading.Lock()
_MAX_PLAN_DAYS = 366
_SNIPPET_LIMIT = 120


def _snippet(text: str, limit: int = _SNIPPET_LIMIT) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()[:limit]


# --------------------------------------------------------------------------
# Behind you - past posts
# --------------------------------------------------------------------------

def past_posts(workspace, config, days: int = 30, today=None) -> dict:
    """Everything posted in the last `days` days, oldest first.

    Returns {"snapshot_latest", "posts", "ledger_ok"}. ledger_ok is False only
    when the posted record does not exist yet. A record that exists with
    nothing in the window is a real, empty answer, not a failure.
    """
    today = today or ws.today_in(config)
    entries = posted_ledger.load_entries(workspace.posted_ledger)
    ledger_ok = workspace.posted_ledger.is_file()
    if not entries:
        return {
            "snapshot_latest": None,
            "posts": [],
            "ledger_ok": ledger_ok,
            "stats_as_of": None,
        }

    cutoff = today - datetime.timedelta(days=days)
    posts = []
    for entry in entries:
        try:
            posted_on = datetime.date.fromisoformat(entry["date"])
        except (KeyError, ValueError):
            continue
        if posted_on < cutoff or posted_on > today:
            continue
        code = entry.get("shortcode")
        thumb = None
        if code and (workspace.thumbs_dir / f"{code}.jpg").is_file():
            thumb = f"{code}.jpg"
        posts.append({
            "date": posted_on.isoformat(),
            "shortCode": code,
            "post_url": entry.get("link") or None,
            "platform": entry.get("platform", ""),
            "format": entry.get("format", ""),
            "title": entry.get("title", ""),
            "caption_snippet": _snippet(entry.get("hook") or entry.get("title") or ""),
            "views": entry.get("views"),
            "likes": entry.get("likes"),
            "comments": entry.get("comments"),
            "stats_as_of": entry.get("stats_as_of"),
            "franchise": entry.get("franchise", ""),
            "thumb": thumb,
        })
    latest = entries[-1]
    return {
        "snapshot_latest": latest["date"],
        "posts": posts,
        "ledger_ok": ledger_ok,
        "stats_as_of": latest.get("stats_as_of"),
    }


# --------------------------------------------------------------------------
# Ahead of you - the plan store
# --------------------------------------------------------------------------

def _load_store(workspace) -> dict:
    data = ws.read_json(workspace.calendar_plan, default=None)
    if not isinstance(data, dict) or not isinstance(data.get("plans"), list):
        return {"plans": []}
    return data


def _validate_date(value, today=None) -> str:
    if not isinstance(value, str):
        raise ValueError("a date is needed, written as YYYY-MM-DD")
    try:
        parsed = datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{value!r} is not a real date written as YYYY-MM-DD")
    reference = today or datetime.date.today()
    if abs((parsed - reference).days) > _MAX_PLAN_DAYS:
        raise ValueError("a plan has to sit within a year of today")
    return parsed.isoformat()


def _validate_title(value) -> str:
    if not isinstance(value, str):
        raise ValueError("a title is needed")
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("a title is needed")
    if len(trimmed) > 200:
        raise ValueError("a title has to be 200 characters or fewer")
    return trimmed


def _validate_note(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("a note has to be text")
    if len(value) > 1000:
        raise ValueError("a note has to be 1000 characters or fewer")
    return value


def _validate_status(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("a status is needed")
    if len(value) > 50:
        raise ValueError("a status has to be 50 characters or fewer")
    return value.strip()


def _new_plan_id(existing) -> str:
    taken = {plan.get("id") for plan in existing}
    for _ in range(10):
        candidate = secrets.token_hex(4)
        if candidate not in taken:
            return candidate
    raise RuntimeError("could not make a unique plan id")


def plans_list(workspace) -> list:
    store = _load_store(workspace)
    return sorted((dict(plan) for plan in store["plans"]), key=lambda p: p.get("date", ""))


def plan_add(workspace, date, title, note="") -> dict:
    date_value = _validate_date(date)
    title_value = _validate_title(title)
    note_value = _validate_note(note)
    with _PLAN_LOCK:
        store = _load_store(workspace)
        plan = {
            "id": _new_plan_id(store["plans"]),
            "date": date_value,
            "title": title_value,
            "note": note_value,
            "status": "planned",
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        store["plans"].append(plan)
        ws.atomic_write_json(workspace.calendar_plan, store)
        return dict(plan)


def plan_update(workspace, plan_id, **fields) -> dict:
    unknown = set(fields) - PLAN_FIELDS
    if unknown:
        raise ValueError(f"unknown field(s): {', '.join(sorted(unknown))}")
    normalized = {}
    if "date" in fields:
        normalized["date"] = _validate_date(fields["date"])
    if "title" in fields:
        normalized["title"] = _validate_title(fields["title"])
    if "note" in fields:
        normalized["note"] = _validate_note(fields["note"])
    if "status" in fields:
        normalized["status"] = _validate_status(fields["status"])
    with _PLAN_LOCK:
        store = _load_store(workspace)
        target = next((p for p in store["plans"] if p.get("id") == plan_id), None)
        if target is None:
            raise ValueError(f"no plan with id {plan_id!r}")
        if normalized:
            target.update(normalized)
            ws.atomic_write_json(workspace.calendar_plan, store)
        return dict(target)


def plan_delete(workspace, plan_id) -> bool:
    with _PLAN_LOCK:
        store = _load_store(workspace)
        before = len(store["plans"])
        store["plans"] = [p for p in store["plans"] if p.get("id") != plan_id]
        if len(store["plans"]) == before:
            return False
        ws.atomic_write_json(workspace.calendar_plan, store)
        return True
