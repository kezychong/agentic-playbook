#!/usr/bin/env python3
"""Read a configured Google Calendar service account with a read-only scope.

This helper is deliberately a subprocess.  Missing Google libraries or a slow
network response cannot unmount or block the Hermes dashboard plugin.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
MAX_EVENTS = 60
MAX_CALENDARS = 40
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")
_LONG_BLOB_RE = re.compile(r"[A-Za-z0-9_-]{24,}")


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = _EMAIL_RE.sub("•••", text)
    text = _LONG_BLOB_RE.sub("•••", text)
    return " ".join(text.split())[:200]


def _iso(value: str, all_day: bool, zone: ZoneInfo) -> str:
    if all_day:
        try:
            day = datetime.strptime(value[:10], "%Y-%m-%d")
        except ValueError:
            return value
        return day.replace(tzinfo=zone).isoformat(timespec="seconds")
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=zone)
    return moment.astimezone(zone).isoformat(timespec="seconds")


def _declined(event: dict) -> bool:
    attendees = event.get("attendees")
    if not isinstance(attendees, list):
        return False
    return any(
        isinstance(person, dict)
        and person.get("self")
        and person.get("responseStatus") == "declined"
        for person in attendees
    )


def collect(service, start: datetime, end: datetime, zone: ZoneInfo) -> tuple[list, int]:
    events = []
    calendars = service.calendarList().list().execute().get("items", [])[:MAX_CALENDARS]
    for calendar in calendars:
        identifier = calendar.get("id")
        if not identifier:
            continue
        answer = service.events().list(
            calendarId=identifier,
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            showDeleted=False,
            maxResults=MAX_EVENTS,
        ).execute()
        for event in answer.get("items", []):
            if event.get("status") == "cancelled" or _declined(event):
                continue
            raw_start = event.get("start") or {}
            raw_end = event.get("end") or {}
            all_day = "dateTime" not in raw_start
            begins = raw_start.get("dateTime") or raw_start.get("date")
            finishes = raw_end.get("dateTime") or raw_end.get("date")
            if not begins:
                continue
            events.append(
                {
                    "title": str(event.get("summary") or "(untitled)")[:200],
                    "start": _iso(str(begins), all_day, zone),
                    "end": _iso(str(finishes), all_day, zone) if finishes else None,
                    "calendar": str(calendar.get("summary") or "")[:120],
                    "allDay": all_day,
                }
            )
    events.sort(key=lambda item: (item["start"], item["allDay"]))
    return events[:MAX_EVENTS], len(calendars)


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--service-account", required=True)
    parser.add_argument("--timezone", required=True)
    parser.add_argument("--hours", required=True, type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = _arguments(argv)
        zone = ZoneInfo(args.timezone)
    except (SystemExit, ZoneInfoNotFoundError):
        json.dump({"error": "invalid calendar configuration"}, sys.stdout)
        return 4
    path = Path(args.service_account).expanduser()
    if not path.is_absolute() or not path.is_file():
        json.dump({"error": "no service account configured"}, sys.stdout)
        return 4
    hours = max(1, min(args.hours, 168))
    try:
        from google.oauth2 import service_account  # type: ignore[import-not-found]
        from googleapiclient.discovery import build  # type: ignore[import-not-found]
    except Exception:
        json.dump({"error": "google client not importable"}, sys.stdout)
        return 3

    now = datetime.now(zone)
    try:
        credentials = service_account.Credentials.from_service_account_file(str(path), scopes=SCOPES)
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        events, calendars = collect(service, now, now + timedelta(hours=hours), zone)
    except Exception as exc:
        json.dump({"error": _safe_error(exc)}, sys.stdout)
        return 5
    json.dump(
        {"events": events, "hours": hours, "calendars": calendars, "at": now.isoformat(timespec="seconds")},
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
