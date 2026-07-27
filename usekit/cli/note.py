# usekit/cli/note.py — uk note command handler
#
# Usage:
#   uk note start [vite_port] [api_port]   start servers (nohup background)
#   uk note stop  [vite_port] [api_port]   stop servers
#   uk note rebuild                        sync src + npm + restart
#   uk note seed [--reset]                 generate test deck
#   uk note status [vite_port] [api_port]  show server status
#
# Delegates actual work to: <project>/shell/note.sh

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


# ── Project root resolution ────────────────────────────────────────────────────

def _get_project_dir() -> str | None:
    """Resolve SRSNOTE project root via usekit env."""
    for key in ("USEKIT_BASE", "BASE_PATH", "PROJECT_PATH"):
        v = os.environ.get(key)
        if v and os.path.isdir(v):
            return v
    try:
        from usekit.classes.core.env.loader_env import get_base_path
        p = str(get_base_path())
        if p and os.path.isdir(p):
            return p
    except Exception:
        pass
    return None


def _find_note_sh(project_dir: str) -> Path | None:
    """Find shell/note.sh under the project root."""
    candidate = Path(project_dir) / "shell" / "note.sh"
    return candidate if candidate.exists() else None


# ── Runner ────────────────────────────────────────────────────────────────────

def run(args: list[str]) -> int:
    """Entry point: uk note <action> [...]"""

    # Whether the request is a help request (no args or an explicit help flag).
    want_help = (not args) or args[0] in ("-h", "--help", "help")

    project_dir = _get_project_dir()
    if not project_dir:
        if want_help:
            _print_usage()   # fallback when we cannot reach the project
            return 0
        print("[uk note] Cannot resolve project directory.")
        print("          Set USEKIT_BASE or run from a usekit project.")
        return 1

    note_sh = _find_note_sh(project_dir)
    if not note_sh:
        if want_help:
            _print_usage()   # fallback when note.sh is unavailable
            return 0
        print(f"[uk note] shell/note.sh not found in: {project_dir}")
        return 1

    # Delegate help to note.sh so its do_help stays the single source of truth
    # (it knows the project-specific actions like service/tunnel).
    if want_help:
        args = ["help"]

    # Forward all args directly to note.sh
    cmd = ["bash", str(note_sh)] + args

    try:
        result = subprocess.run(cmd, cwd=project_dir)
        return result.returncode
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"[uk note] {e}")
        return 1


# ── Help ──────────────────────────────────────────────────────────────────────

def _print_usage():
    print("""uk note — SRSNOTE server controller

Usage:
    uk note start   [vite_port] [api_port]   start servers (default 5173 8100)
    uk note stop    [vite_port] [api_port]   stop servers
    uk note rebuild                          sync src + npm + restart
    uk note seed    [--reset]                generate test deck
    uk note status  [vite_port] [api_port]   show running status

Examples:
    uk note start                  start on default ports (5173 / 8100)
    uk note start 5174 8101        start on custom ports
    uk note stop                   stop default port servers
    uk note stop 5174 8101         stop custom port servers
    uk note rebuild                full rebuild + restart
    uk note seed                   generate test deck (8 cards)
    uk note seed --reset           reset DB then generate
    uk note status                 check server status

Ports:
    5173  Vite (React UI)   — default
    8100  API (Python)      — default
    7979  usekit editor     — separate (uk editor)""")
