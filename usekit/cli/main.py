# Path: usekit.cli.main
# ---------------------------------------------------------------------------
#  CLI entry point for usekit.
#  Thin proxy: parses terminal args -> calls u.xxx() directly.
#
#  Usage:
#      uk wtb memo "hello"          # one-shot
#      uk repl                      # interactive REPL
#      uk urjb config               # u-prefix shorthand
#
#  Created by: The Little Prince x ROP x FOP
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
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
    uk repl                       interactive mode

Commands (action + format + location):
    Action:  r(read) w(write) u(update) d(delete) h(has)
             e(emit) p(path) f(find) l(list) g(get) s(set)
             x(exec) i(import)
    Format:  j(json) y(yaml) c(csv) t(txt) m(md)
             s(sql) d(ddl) p(pyp) k(km) a(any)
    Location: b(base) s(sub) d(dir) n(now) t(tmp)
              p(pre) c(cache) m(mem)

Examples:
    uk wtb memo "hello world"           write txt to base
    uk wjb config '{"name":"usekit"}'   write json to base
    uk rjb config                       read json from base
    uk urjb config                      same (u-prefix)
    uk ljb                              list json in base
    uk hjb config                       check if exists
    uk ejm '{"a":1}'                    emit json (memory)
    uk xsb "select * from t"            exec sql on base
    uk repl                             start REPL""")


def _print_version():
    try:
        from importlib.metadata import version
        v = version("usekit")
    except Exception:
        v = "unknown"
    print(f"usekit {v}")


if __name__ == "__main__":
    sys.exit(main())
