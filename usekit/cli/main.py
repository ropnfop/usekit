# Path: usekit.cli.main
# ---------------------------------------------------------------------------
#  CLI entry point for usekit.
#  Thin proxy: parses terminal args -> calls u.xxx() directly.
#
#  Usage:
#      uk wtb memo "hello"          # one-shot
#      uk ai claude "explain this"  # AI agent bridge
#      uk repl                      # interactive REPL
#      uk urjb config               # u-prefix shorthand
#
#  Created by: The Little Prince x ROP x FOP
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any


# ---------------------------------------------------------------
# Argument classification
# ---------------------------------------------------------------

# Operations that require <name> argument
_NEED_NAME = {"r", "d", "h"}

# Operations that require <name> + <data>
_NEED_NAME_DATA = {"w", "u", "s"}

# Operations that accept optional <name>
_OPTIONAL_NAME = {"p", "f", "l", "g"}

# Operations that require <data> only
_EMIT_OPS = {"e"}

# Exec operations
_EXEC_OPS = {"x", "i", "b", "c"}


def _try_parse_json(value: str) -> Any:
    """Attempt JSON parse; return raw string on failure."""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def _format_result(result: Any) -> str:
    """Format result for terminal output."""
    if result is None:
        return ""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, indent=2, default=str)
    return str(result)


def _import_usekit():
    """Import usekit (banner suppressed via USEKIT_QUIET env var)."""
    from usekit import u
    return u


# ---------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------

def main() -> int:
    """CLI entry point."""
    args = sys.argv[1:]

    if not args:
        _print_usage()
        return 0

    cmd = args[0].lower()

    # -- Help / Version / REPL --
    if cmd in ("-h", "--help", "help"):
        _print_usage()
        return 0

    if cmd in ("-v", "--version", "version"):
        _print_version()
        return 0

    if cmd in ("repl", "shell"):
        return _run_repl()

    # -- AI agent commands --
    # uk ai claude "prompt"
    # uk ai codex  "prompt"
    if cmd == "ai":
        return _run_ai(args[1:])

    # -- Verify command (mechanical CHECK-block validation) --
    if cmd == "verify":
        from usekit.cli.verify import run as _run_verify
        return _run_verify(args[1:])

    # -- Project commands --
    if cmd == "note":
        from usekit.cli.note import run as _run_note
        return _run_note(args[1:])

    # -- Utility commands --
    if cmd == "setup":
        return _run_util("setup")

    if cmd == "check":
        return _run_util("check")

    if cmd == "editor":
        # uk editor            → start (nohup background)
        # uk editor stop       → stop server
        # uk editor status     → check status
        sub = args[1].lower() if len(args) > 1 else ""
        if sub in ("stop", "status", "stat"):
            from usekit.cli.editor import run as _run_editor
            return _run_editor(args[1:])
        # Start: spawn as nohup background process so CLI returns immediately
        from usekit.cli.editor import do_start
        return do_start()

    if cmd == "termux":
        return _run_util("termux")

    # -- Autostart on/off --
    if cmd == "autostart":
        return _run_autostart(args[1:])

    # -- Validate command --
    # 4-letter u-prefix shorthand: urjb -> rjb
    if len(cmd) == 4 and cmd[0] == "u":
        cmd = cmd[1:]

    if len(cmd) != 3:
        print(f"[usekit] Invalid command: '{args[0]}'")
        print(f"         Must be 3 letters: <action><format><location>")
        print(f"         Example: uk wtb memo \"hello\"")
        return 1

    return _run_command(cmd, args[1:])


def _run_command(cmd: str, rest_args: list) -> int:
    """Execute a single 3-letter command."""
    u = _import_usekit()
    op = cmd[0]

    try:
        method = getattr(u, cmd)
    except AttributeError as exc:
        print(f"[usekit] {exc}")
        return 1

    # -- Argument validation --
    if op in _NEED_NAME and not rest_args:
        print(f"[usekit] Missing argument: name\n")
        print(f"  Usage:   uk {cmd} <name>")
        print(f"  Example: uk {cmd} config")
        return 1

    if op in _NEED_NAME_DATA:
        if len(rest_args) < 1:
            print(f"[usekit] Missing arguments: name, data\n")
            print(f"  Usage:   uk {cmd} <name> <data>")
            print(f"  Example: uk {cmd} config '{{\"key\": \"value\"}}'")
            return 1
        if len(rest_args) < 2:
            print(f"[usekit] Missing argument: data\n")
            print(f"  Usage:   uk {cmd} <name> <data>")
            print(f"  Example: uk {cmd} {rest_args[0]} '{{\"key\": \"value\"}}'")
            return 1

    if op in _EMIT_OPS and not rest_args:
        print(f"[usekit] Missing argument: data\n")
        print(f"  Usage:   uk {cmd} <data> [type]")
        print(f"  Example: uk {cmd} '{{\"key\": \"value\"}}'")
        return 1

    # -- Route by operation type --
    try:
        if op in _NEED_NAME_DATA:
            result = _handle_write(method, cmd, rest_args)
        elif op in _NEED_NAME or op in _OPTIONAL_NAME:
            result = _handle_read(method, cmd, rest_args)
        elif op in _EMIT_OPS:
            result = _handle_emit(method, cmd, rest_args)
        elif op in _EXEC_OPS:
            result = _handle_exec(method, cmd, rest_args)
        else:
            print(f"[usekit] Unknown operation: '{op}'")
            return 1

        output = _format_result(result)
        if output:
            print(output)
        return 0

    except Exception as exc:
        print(f"[usekit] {exc}")
        return 1


# ---------------------------------------------------------------
# Operation handlers
# ---------------------------------------------------------------

def _handle_write(method, cmd: str, args: list) -> Any:
    """write/update/set: uk wjb <name> <data>"""
    name = args[0]
    raw_data = " ".join(args[1:])
    data = _try_parse_json(raw_data)
    return method(data=data, name=name)


def _handle_read(method, cmd: str, args: list) -> Any:
    """read/get/path/find/list/delete/has: uk rjb [name] [keydata]"""
    op = cmd[0]

    if not args:
        return method()

    name = args[0]

    # get/read with keydata
    if len(args) >= 2 and op in ("r", "g"):
        return method(name=name, keydata=args[1])

    return method(name=name)


def _handle_emit(method, cmd: str, args: list) -> Any:
    """emit: uk ejm <data> [type]"""
    raw_data = args[0]
    data = _try_parse_json(raw_data)

    if len(args) >= 2:
        return method(data=data, type=args[1])

    return method(data=data)


def _handle_exec(method, cmd: str, args: list) -> Any:
    """exec/import/boot/close: uk xsb <code/sql>"""
    if not args:
        return method()

    raw = " ".join(args)
    data = _try_parse_json(raw)
    return method(data)


# ---------------------------------------------------------------
# AI agent commands
# ---------------------------------------------------------------

# Provider configs: name -> how to spawn CLI
_AI_PROVIDERS = {
    "claude": {
        "cli_resolve": lambda: _find_claude_cli(),
        "args": lambda prompt, opts: _build_claude_args(prompt, opts),
    },
    # Future:
    # "codex":  { ... },
    # "gemini": { ... },
}

# Session file for --continue
_SESSION_FILE = os.path.expanduser("~/.usekit/last_session")


def _build_claude_args(prompt: str, opts: dict) -> list[str]:
    """Build Claude Code CLI arguments with optional flags."""
    args = ["-p", prompt, "--output-format", "stream-json", "--verbose",
            "--permission-mode", "bypassPermissions"]

    if opts.get("continue"):
        args.append("--continue")
    elif opts.get("session"):
        args.extend(["--resume", opts["session"]])

    if opts.get("model"):
        args.extend(["--model", opts["model"]])

    return args


def _get_project_dir() -> str | None:
    """Resolve project root for CLI cwd."""
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


def _save_session_id(session_id: str):
    """Save last session ID for --continue fallback."""
    try:
        os.makedirs(os.path.dirname(_SESSION_FILE), exist_ok=True)
        with open(_SESSION_FILE, "w") as f:
            f.write(session_id)
    except Exception:
        pass


def _load_session_id() -> str | None:
    """Load last session ID."""
    try:
        with open(_SESSION_FILE) as f:
            return f.read().strip() or None
    except Exception:
        return None


def _find_claude_cli() -> list[str] | None:
    """Locate Claude Code cli.js. Returns [node, cli.js] or None."""
    try:
        root = subprocess.check_output(
            ["npm", "root", "-g"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        cli_path = os.path.join(root, "@anthropic-ai", "claude-code", "cli.js")
        if os.path.isfile(cli_path):
            return ["node", cli_path]
    except Exception:
        pass
    return None


def _run_ai(args: list[str]) -> int:
    """Route: uk ai <provider> [options] <prompt...>

    Options:
        -c, --continue      Continue last conversation
        -r, --resume <id>   Resume specific session
        --model <model>     Model override (full name)
    """

    if not args:
        _print_ai_usage()
        return 0

    provider = args[0].lower()

    if provider in ("-h", "--help", "help"):
        _print_ai_usage()
        return 0

    if provider not in _AI_PROVIDERS:
        print(f"[usekit] Unknown AI provider: '{provider}'")
        print(f"         Available: {', '.join(_AI_PROVIDERS)}")
        return 1

    # Parse options from remaining args
    rest = args[1:]
    opts = {}
    prompt_parts = []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in ("-c", "--continue"):
            opts["continue"] = True
        elif a in ("-r", "--resume"):
            if i + 1 < len(rest) and not rest[i + 1].startswith("-"):
                i += 1
                opts["session"] = rest[i]
            else:
                # --resume without ID: use last session
                sid = _load_session_id()
                if sid:
                    opts["session"] = sid
                else:
                    print("[usekit] No session to resume.")
                    return 1
        elif a == "--model":
            if i + 1 < len(rest):
                i += 1
                opts["model"] = rest[i]
            else:
                print("[usekit] --model requires a value.")
                return 1
        else:
            prompt_parts.append(a)
        i += 1

    prompt = " ".join(prompt_parts)

    if not prompt:
        print(f"[usekit] Missing prompt.")
        print(f"  Usage: uk ai {provider} \"your prompt here\"")
        return 1

    cfg = _AI_PROVIDERS[provider]

    # Resolve CLI path
    cli_cmd = cfg["cli_resolve"]()
    if cli_cmd is None:
        print(f"[usekit] {provider} CLI not found.")
        if provider == "claude":
            print("  Install: npm install -g @anthropic-ai/claude-code@1.0.33")
        return 1

    # Build full command
    full_cmd = cli_cmd + cfg["args"](prompt, opts)

    # Run and stream
    return _stream_ai(full_cmd, provider)


def _stream_ai(cmd: list[str], provider: str) -> int:
    """Spawn AI CLI, parse JSON Lines, print result."""
    cwd = _get_project_dir()
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            cwd=cwd,
        )
    except FileNotFoundError:
        print(f"[usekit] Failed to spawn {provider} CLI.")
        return 1

    result_text = ""
    has_error = False
    session_id = None

    # Stream stdout line by line
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = obj.get("type")

        # Capture session_id from any message
        if "session_id" in obj and obj["session_id"]:
            session_id = obj["session_id"]

        # assistant -> print delta (streaming feel)
        if msg_type == "assistant":
            content = obj.get("message", {}).get("content")
            if isinstance(content, list):
                for block in content:
                    if block.get("type") == "text" and block.get("text"):
                        print(block["text"], end="", flush=True)
            elif isinstance(content, str) and content:
                print(content, end="", flush=True)

        # result -> capture final
        elif msg_type == "result":
            if obj.get("is_error"):
                has_error = True
                result_text = obj.get("result", "Unknown error")
            else:
                result_text = obj.get("result", "")

    proc.wait()

    # Save session_id for --continue
    if session_id:
        _save_session_id(session_id)

    # Print newline after streaming
    print()

    # If streaming didn't print anything, show result
    # (in case assistant messages were empty)
    if has_error:
        print(f"\n[usekit] Error: {result_text}")
        return 1

    # stderr warnings (non-fatal)
    stderr_out = proc.stderr.read().strip()
    if stderr_out and proc.returncode != 0:
        print(f"\n[usekit] {stderr_out}", file=sys.stderr)

    return proc.returncode or 0


def _print_ai_usage():
    print("""usekit AI — Agent CLI bridge

Usage:
    uk ai <provider> <prompt>
    uk ai <provider> -c <prompt>          continue last session
    uk ai <provider> -r <id> <prompt>     resume specific session
    uk ai <provider> --model <m> <prompt> model override

Providers:
    claude      Claude Code (v1.0.33, cli.js)

Options:
    -c, --continue          Continue last conversation
    -r, --resume [id]       Resume session (omit id for last)
    --model <model>         Full model name

Examples:
    uk ai claude "Explain this code"
    uk ai claude -c "Continue from there"
    uk ai claude --model claude-sonnet-4-20250514 "Analyze"

Note:
    Provider CLI must be installed and authenticated separately.
    usekit does not provide AI access.
    usekit connects to AI CLIs installed by the user.""")


# ---------------------------------------------------------------
# Autostart on/off
# ---------------------------------------------------------------

def _run_autostart(args: list) -> int:
    """Toggle editor autostart in .bashrc.

    Usage:
        uk autostart on
        uk autostart off
        uk autostart        (show current status)
    """
    from pathlib import Path

    bashrc = Path.home() / '.bashrc'
    autostart_line = 'nohup python -c "from usekit import u; u.editor()" > $TMPDIR/editor.log 2>&1 &'

    def _is_on():
        if bashrc.exists():
            return 'u.editor()' in bashrc.read_text()
        return False

    if not args:
        status = "on" if _is_on() else "off"
        print(f"[usekit] Editor autostart: {status}")
        return 0

    action = args[0].lower()

    if action == "on":
        if _is_on():
            print("[usekit] Editor autostart already on")
        else:
            with open(bashrc, 'a') as f:
                f.write(f'\n{autostart_line}\n')
            print("[usekit] ✓ Editor autostart enabled")
        return 0

    if action == "off":
        if not _is_on():
            print("[usekit] Editor autostart already off")
        else:
            lines = bashrc.read_text().splitlines(keepends=True)
            lines = [l for l in lines if 'u.editor()' not in l]
            bashrc.write_text(''.join(lines))
            print("[usekit] ✓ Editor autostart disabled")
        return 0

    print(f"[usekit] Usage: uk autostart [on|off]")
    return 1


# ---------------------------------------------------------------
# Utility commands (setup, check, editor, termux)
# ---------------------------------------------------------------

def _run_util(cmd: str) -> int:
    """Run utility commands: setup, check, editor, termux."""
    try:
        from usekit.classes.wrap.base.use_interface import (
            setup, check, editor, termux,
        )
        _UTIL_MAP = {
            "setup": setup,
            "check": check,
            "editor": editor,
            "termux": termux,
        }
        fn = _UTIL_MAP.get(cmd)
        if fn is None:
            print(f"[usekit] Unknown utility: '{cmd}'")
            return 1

        result = fn()
        return 0 if result else 1

    except Exception as e:
        print(f"[usekit] {cmd} failed: {e}")
        return 1


# ---------------------------------------------------------------
# REPL
# ---------------------------------------------------------------

def _run_repl() -> int:
    """Interactive REPL mode.

    usekit> rjb config
    usekit> wjb test {"a":1}
    usekit> q
    """
    print("usekit REPL (type 'q' to quit, 'help' for usage)\n")

    while True:
        try:
            line = input("usekit> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        if line in ("q", "quit", "exit"):
            break

        if line in ("help", "h", "?"):
            _print_usage()
            continue

        # Parse: first token = cmd, rest = args
        parts = line.split()
        cmd = parts[0].lower()

        # u-prefix shorthand in REPL too
        if len(cmd) == 4 and cmd[0] == "u":
            cmd = cmd[1:]

        if len(cmd) != 3:
            print(f"  Invalid: '{parts[0]}' -- need 3-letter command")
            continue

        _run_command(cmd, parts[1:])

    return 0


# ---------------------------------------------------------------
# Help / Version
# ---------------------------------------------------------------

def _print_usage():
    print("""usekit CLI - Memory-Oriented Software Architecture

Usage:
    uk <cmd> [name] [data]        one-shot command
    uk u<cmd> [name] [data]       u-prefix shorthand
    uk ai <provider> <prompt>     AI agent bridge
    uk repl                       interactive mode

Setup & Utils:
    uk setup                      interactive workspace setup
    uk check                      verify environment status
    uk editor                     launch editor (port 7979)
    uk editor stop               stop editor server
    uk editor status             check editor status
    uk autostart on|off           toggle editor autostart
    uk termux                     setup Termux storage

Project:
    uk note start [vite] [api]    start SRSNOTE servers
    uk note stop  [vite] [api]    stop SRSNOTE servers
    uk note rebuild               sync + npm + restart
    uk note seed [--reset]        generate test deck
    uk note status                show server status

Commands (action + format + location):
    Action:  r(read) w(write) u(update) d(delete) h(has)
             e(emit) p(path) f(find) l(list) g(get) s(set)
             x(exec) i(import)
    Format:  j(json) y(yaml) c(csv) t(txt) m(md)
             s(sql) d(ddl) p(pyp) k(km) a(any)
    Location: b(base) s(sub) d(dir) n(now) t(tmp)
              p(pre) c(cache) m(mem)

AI Providers:
    uk ai claude "prompt"         Claude Code
    uk ai help                    show AI help

Examples:
    uk setup                            first-time workspace setup
    uk wtb memo "hello world"           write txt to base
    uk wjb config '{"name":"usekit"}'   write json to base
    uk rjb config                       read json from base
    uk urjb config                      same (u-prefix)
    uk ljb                              list json in base
    uk hjb config                       check if exists
    uk ejm '{"a":1}'                    emit json (memory)
    uk xsb "select * from t"            exec sql on base
    uk ai claude "Explain this code"    ask Claude""")


def _print_version():
    try:
        from importlib.metadata import version
        v = version("usekit")
    except Exception:
        v = "unknown"
    print(f"usekit {v}")


if __name__ == "__main__":
    sys.exit(main())
