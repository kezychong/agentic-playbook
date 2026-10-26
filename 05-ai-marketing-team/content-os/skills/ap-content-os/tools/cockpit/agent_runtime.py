#!/usr/bin/env python3
"""
agent_runtime.py - can this machine run a stage step on its own, or does the
member paste the step to their assistant?

Standard library only.

The cockpit's step buttons carry the same request either way. What changes is
only how the request gets to an agent:

  driveable   an assistant is already installed on this machine and can be
              handed the step to run quietly in the background. The button
              runs it. The member sees a progress line and a receipt.

  copy        no such assistant is installed. The same button shows the exact
              request as a block to copy and paste into the app the member is
              already using. Same words, one extra click.

The wording of every step lives in one place, board_state.py, so both paths
are byte-identical. The capability changes the ergonomics, never the work.

What a driven step is allowed to do is deliberately narrow: read and write
files, and a handful of safe local file commands. Nothing that can reach the
network. Idea cards can carry text copied off the open internet, and text
copied off the internet never gets handed a tool that can phone out.
"""

import os
import shutil
import subprocess
import threading

STEP_TIMEOUT_SECONDS = 900  # fifteen minutes, then the step is stopped

# File work and safe local file commands only. Nothing outbound.
ALLOWED_TOOLS = [
    "Read", "Glob", "Grep", "Edit", "Write", "MultiEdit", "Skill", "TodoWrite",
    "Bash(mv:*)", "Bash(mkdir:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(cp:*)",
]

ENV_AGENT = "CONTENT_OS_COCKPIT_AGENT"

_LOCK = threading.Lock()
_DETECTED = None


def _claude_argv(binary: str, prompt: str):
    return [
        binary, "-p", prompt,
        "--permission-mode", "acceptEdits",
        "--allowedTools", *ALLOWED_TOOLS,
    ]


def _codex_argv(binary: str, prompt: str):
    return [binary, "exec", "--skip-git-repo-check", prompt]


RUNTIMES = [
    {"id": "claude", "command": "claude", "label": "the assistant app", "argv": _claude_argv},
    {"id": "codex", "command": "codex", "label": "the assistant app", "argv": _codex_argv},
]


def detect(force: bool = False) -> dict:
    """Which runtime, if any, this machine can drive.

    Returns {"mode": "run"|"copy", "id": str, "binary": str, "label": str}.

    The answer is worked out once and remembered, because it cannot change
    while the cockpit is open. Setting CONTENT_OS_COCKPIT_AGENT to "off"
    forces the copy path; setting it to a runtime name pins that one.
    """
    global _DETECTED
    with _LOCK:
        if _DETECTED is not None and not force:
            return dict(_DETECTED)

        preference = (os.environ.get(ENV_AGENT, "off") or "off").strip().lower()
        result = {"mode": "copy", "id": "", "binary": "", "label": ""}

        if preference not in ("off", "none", "copy"):
            candidates = RUNTIMES
            if preference not in ("", "auto"):
                candidates = [r for r in RUNTIMES if r["id"] == preference]
            for runtime in candidates:
                binary = shutil.which(runtime["command"])
                if binary:
                    result = {
                        "mode": "run",
                        "id": runtime["id"],
                        "binary": binary,
                        "label": runtime["label"],
                    }
                    break
        _DETECTED = dict(result)
        return dict(result)


def build_argv(prompt: str):
    """The exact command a driven step runs, or None when this machine has
    no runtime to drive."""
    detected = detect()
    if detected["mode"] != "run":
        return None
    runtime = next((r for r in RUNTIMES if r["id"] == detected["id"]), None)
    if runtime is None:
        return None
    return runtime["argv"](detected["binary"], prompt)


def run_step(prompt: str, cwd, log_path):
    """Run one step quietly in the background and wait for it to finish.

    Everything the step prints goes into its own log file. A step still
    running after the time limit is stopped, so nothing can sit there
    forever. Raises RuntimeError on any failure, which the caller records on
    the job and surfaces to the member once.
    """
    argv = build_argv(prompt)
    if argv is None:
        raise RuntimeError("no assistant on this machine can be handed this step")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            argv,
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        try:
            returncode = process.wait(timeout=STEP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RuntimeError(
                f"the step was stopped after {STEP_TIMEOUT_SECONDS // 60} minutes"
            )
    if returncode != 0:
        raise RuntimeError(f"the step ended with an error, see {log_path.name}")
