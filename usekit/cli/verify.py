# usekit/cli/verify.py — uk verify command handler
#
# Usage:
#   uk verify <check_file>     run a CHECK block file (mechanical layer-1 verify)
#   uk verify -                read CHECK block from stdin
#
# CHECK block syntax (one check per line; #/blank ignored):
#   root: <abs path>           base dir for relative file paths below
#   node: <file.js>            node --check must pass
#   grep0: <file> <pattern>    match count must be 0
#   grepc: <file> <pattern> N  match count must equal N
#   grepge: <file> <pattern> N match count must be >= N
#   divbalance: <file.html>    count('<div') must equal count('</div>')
#
# Job report and self-claims are NOT trusted — this reads the disk directly.

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def _count(path: str, pattern: str) -> int:
    """Count lines in file matching the (extended) regex pattern."""
    try:
        text = Path(path).read_text(errors="replace")
    except Exception:
        return -1  # file unreadable
    rx = re.compile(pattern)
    return sum(1 for line in text.splitlines() if rx.search(line))


def _node_check(path: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(["node", "--check", path],
                           capture_output=True, text=True)
        return (r.returncode == 0, (r.stderr or r.stdout).strip().splitlines()[0]
                if r.returncode != 0 and (r.stderr or r.stdout).strip() else "")
    except FileNotFoundError:
        return (False, "node not found")
    except Exception as e:
        return (False, str(e))


def _abspath(root: str, f: str) -> str:
    return f if os.path.isabs(f) else os.path.join(root, f)


def run(args: list[str]) -> int:
    """Entry: uk verify <check_file> | uk verify -"""
    if not args or args[0] in ("-h", "--help", "help"):
        _print_usage()
        return 0

    src = args[0]
    if src == "-":
        lines = sys.stdin.read().splitlines()
    else:
        p = Path(src)
        if not p.is_file():
            print(f"  ✗ CHECK file not found: {src}")
            return 1
        lines = p.read_text(errors="replace").splitlines()

    print(f"\n  ◆ usekit verify")
    print(f"  {'─' * 38}")

    root = os.getcwd()
    npass = 0
    nfail = 0

    def ok(label: str, detail: str):
        nonlocal npass
        npass += 1
        print(f"  ✓ {label:<10} {detail}")

    def bad(label: str, detail: str):
        nonlocal nfail
        nfail += 1
        print(f"  ✗ {label:<10} {detail}")

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # allow CHECK blocks that are fenced or headed; skip non-directive lines
        if ":" not in s:
            continue
        cmd, _, rest = s.partition(":")
        cmd = cmd.strip().lower()
        rest = rest.strip()

        if cmd == "root":
            root = rest
            print(f"  · root = {root}")
        elif cmd == "node":
            f = _abspath(root, rest)
            if not os.path.isfile(f):
                bad("node", f"{rest} (파일없음)")
            else:
                good, err = _node_check(f)
                ok("node", rest) if good else bad("node", f"{rest} ({err or '문법오류'})")
        elif cmd == "grep0":
            parts = rest.split()
            f = parts[0]; pat = " ".join(parts[1:])
            n = _count(_abspath(root, f), pat)
            if n < 0: bad("grep0", f"{f} (파일없음)")
            elif n == 0: ok("grep0", f"{f}  /{pat}/ = 0")
            else: bad("grep0", f"{f}  /{pat}/ = {n} (0이어야)")
        elif cmd in ("grepc", "grepge"):
            parts = rest.split()
            if len(parts) < 3:
                bad(cmd, f"인자부족: {rest}"); continue
            f = parts[0]; exp = parts[-1]; pat = " ".join(parts[1:-1])
            try:
                exp_n = int(exp)
            except ValueError:
                bad(cmd, f"기대값 정수아님: {exp}"); continue
            n = _count(_abspath(root, f), pat)
            if n < 0:
                bad(cmd, f"{f} (파일없음)")
            elif (cmd == "grepc" and n == exp_n) or (cmd == "grepge" and n >= exp_n):
                op = "==" if cmd == "grepc" else ">="
                ok(cmd, f"{f}  /{pat}/ = {n} ({op}{exp_n})")
            else:
                op = "==" if cmd == "grepc" else ">="
                bad(cmd, f"{f}  /{pat}/ = {n} (기대 {op}{exp_n})")
        elif cmd == "divbalance":
            f = _abspath(root, rest)
            try:
                t = Path(f).read_text(errors="replace")
                o = len(re.findall(r"<div", t))
                c = len(re.findall(r"</div>", t))
                ok("divbalance", f"{rest}  <div>={o} </div>={c}") if o == c \
                    else bad("divbalance", f"{rest}  <div>={o} </div>={c} (불균형)")
            except Exception:
                bad("divbalance", f"{rest} (파일없음)")
        else:
            # unknown directive line — ignore silently (could be prose)
            continue

    print(f"  {'─' * 38}")
    total = npass + nfail
    print(f"  total {total}  ✓ {npass}  ✗ {nfail}\n")
    return 0 if nfail == 0 else 1


def _print_usage():
    print("""uk verify — mechanical CHECK-block validator (layer-1)

Usage:
    uk verify <check_file>     run a CHECK block file
    uk verify -                read CHECK block from stdin

CHECK syntax (one per line; #/blank ignored):
    root: <abs path>           base dir for relative paths below
    node: <file.js>            node --check must pass
    grep0: <file> <pattern>    match count must be 0
    grepc: <file> <pattern> N  match count == N
    grepge: <file> <pattern> N match count >= N
    divbalance: <file.html>    count('<div') == count('</div>')

Notes:
    Reads disk directly — does not trust job/self reports.
    Exit code 0 if all pass, 1 if any fail.""")