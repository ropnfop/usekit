# usekit/cli/editor.py — uk editor command handler (stop / status)
#
# Usage:
#   uk editor              start editor (existing behavior)
#   uk editor stop         kill editor server on port 7979
#   uk editor status       check if editor is running

from __future__ import annotations

import os
import socket


HOST = "127.0.0.1"
PORT = 7979


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_listening() -> bool:
    """Check if port 7979 is open."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        return s.connect_ex((HOST, PORT)) == 0
    finally:
        s.close()


def _is_our_server() -> bool:
    """Verify port 7979 is the usekit editor via /api/ping."""
    try:
        import urllib.request, json
        with urllib.request.urlopen(
            f"http://{HOST}:{PORT}/api/ping", timeout=1.0
        ) as r:
            data = json.loads(r.read())
            return bool(data.get("ok"))
    except Exception:
        return False


def _kill_port() -> bool:
    """Force-kill the editor server on port 7979.

    Order matters on Android/Termux: ss and /proc/net/tcp need socket info
    that Android blocks (netlink / /proc/net permission denied). So we try
    cmdline matching FIRST -- reading /proc/<pid>/cmdline is allowed -- and
    fall back to the socket-based methods on desktop Linux.
    """
    killed = False

    # Method 0: cmdline match (Termux-safe; no socket/netlink access needed).
    # The editor is launched as `... -c from usekit import u; u.editor()`
    # or via open_editor. Match those signatures, skip ourselves.
    try:
        import glob
        self_pid = os.getpid()
        needles = ("u.editor()", "open_editor", "usekit import u")
        for cmd_file in glob.glob("/proc/[0-9]*/cmdline"):
            try:
                pid = int(cmd_file.split("/")[2])
            except Exception:
                continue
            if pid == self_pid:
                continue
            try:
                with open(cmd_file, "rb") as f:
                    # cmdline args are NUL-separated; join to a scanable string
                    cmd = f.read().replace(b"\x00", b" ").decode("utf-8", "ignore")
            except Exception:
                continue
            if any(n in cmd for n in needles):
                try:
                    os.kill(pid, 15)        # SIGTERM
                    killed = True
                except Exception:
                    pass
        if killed:
            # give it a beat, then SIGKILL any survivor still matching
            import time
            time.sleep(0.4)
            for cmd_file in glob.glob("/proc/[0-9]*/cmdline"):
                try:
                    pid = int(cmd_file.split("/")[2])
                    if pid == self_pid:
                        continue
                    with open(cmd_file, "rb") as f:
                        cmd = f.read().replace(b"\x00", b" ").decode("utf-8", "ignore")
                    if any(n in cmd for n in needles):
                        os.kill(pid, 9)     # SIGKILL
                except Exception:
                    pass
            return True
    except Exception:
        pass

    # Method 1: ss
    try:
        import subprocess
        out = subprocess.check_output(
            ["ss", "-tlnp", f"sport = :{PORT}"],
            stderr=subprocess.DEVNULL, text=True
        )
        import re
        m = re.search(r'pid=(\d+)', out)
        if m:
            os.kill(int(m.group(1)), 15)
            killed = True
    except Exception:
        pass

    if killed:
        return True

    # Method 2: /proc/net/tcp scan
    try:
        hex_port = f"{PORT:04X}"
        inode = None
        for tcp_file in ("/proc/net/tcp", "/proc/net/tcp6"):
            try:
                with open(tcp_file) as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) > 9 and f":{hex_port}" in parts[1]:
                            inode = parts[9]
                            break
            except Exception:
                pass
            if inode:
                break

        if inode:
            import glob
            for fddir in glob.glob("/proc/[0-9]*/fd"):
                try:
                    fds = os.listdir(fddir)
                    for fd in fds:
                        try:
                            link = os.readlink(f"{fddir}/{fd}")
                            if f"socket:[{inode}]" in link:
                                pid = int(fddir.split("/")[2])
                                os.kill(pid, 15)
                                return True
                        except Exception:
                            pass
                except Exception:
                    pass
    except Exception:
        pass

    # Method 3: ps-based — find our own editor process by command line.
    # Works on Termux where /proc fd traversal is permission-denied for
    # other users' processes. We launched the editor, so we own it.
    try:
        import subprocess, re
        out = subprocess.check_output(["ps", "-Ao", "pid,args"],
                                       stderr=subprocess.DEVNULL, text=True)
        for line in out.splitlines():
            if "open_editor" in line and "grep" not in line:
                m = re.match(r"\s*(\d+)\s+", line)
                if m:
                    try:
                        os.kill(int(m.group(1)), 15)
                        return True
                    except ProcessLookupError:
                        pass
    except Exception:
        pass

    return False


# ── Commands ──────────────────────────────────────────────────────────────────

def do_start() -> int:
    """Start editor as nohup background process."""
    import subprocess, os
    from pathlib import Path

    print(f"\n  ◆ usekit editor Start (port {PORT})")
    print(f"  {'─' * 38}")

    # Already running?
    if _is_listening():
        if _is_our_server():
            print(f"  - Already running → http://{HOST}:{PORT}")
            # Open browser anyway
            try:
                subprocess.Popen(
                    ["termux-open-url", f"http://{HOST}:{PORT}"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception:
                pass
            print()
            return 0
        else:
            print(f"  ✗ Port {PORT} occupied by a different process")
            print()
            return 1

    # Resolve log path
    log_dir = None
    try:
        for key in ("USEKIT_BASE", "BASE_PATH", "PROJECT_PATH"):
            v = os.environ.get(key)
            if v and os.path.isdir(v):
                log_dir = Path(v) / "logs"
                break
        if not log_dir:
            from usekit.classes.core.env.loader_env import get_base_path
            log_dir = Path(str(get_base_path())) / "logs"
    except Exception:
        log_dir = Path.home() / ".usekit" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "usekit_editor.log"
    pid_file = log_dir / "usekit_editor.pid"

    # Spawn nohup background
    cmd = [
        "python", "-c",
        "from usekit.tools.editor.open_editor import main; main()"
    ]
    with open(log_file, "a") as lf:
        proc = subprocess.Popen(
            cmd,
            stdout=lf, stderr=lf,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    pid_file.write_text(str(proc.pid))

    # Wait for server to be ready
    import time
    for _ in range(20):
        time.sleep(0.4)
        if _is_listening() and _is_our_server():
            break

    if _is_our_server():
        try:
            subprocess.Popen(
                ["termux-open-url", f"http://{HOST}:{PORT}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass
        print(f"  ✓ Editor → http://{HOST}:{PORT}")
        print(f"    log: {log_file}")
    else:
        print(f"  ✗ Editor failed to start — check log: {log_file}")
        print()
        return 1

    print(f"  Stop:    uk editor stop")
    print()
    return 0

def do_stop() -> int:
    import os
    from pathlib import Path

    print(f"\n  ◆ usekit editor Stop (port {PORT})")
    print(f"  {'─' * 38}")

    if not _is_listening():
        print(f"  - Editor not running on port {PORT}")
        print()
        return 0

    if not _is_our_server():
        print(f"  ✗ Port {PORT} is in use by a different process.")
        print(f"    Manual: ps aux | grep u.editor  →  kill -9 <PID>")
        print()
        return 1

    # Try pid file first
    killed = False
    try:
        for key in ("USEKIT_BASE", "BASE_PATH", "PROJECT_PATH"):
            v = os.environ.get(key)
            if v:
                pid_file = Path(v) / "logs" / "usekit_editor.pid"
                if pid_file.exists():
                    pid = int(pid_file.read_text().strip())
                    os.kill(pid, 15)
                    pid_file.unlink(missing_ok=True)
                    killed = True
                    break
    except Exception:
        pass

    # Fallback: port scan
    if not killed:
        killed = _kill_port()

    if killed:
        print(f"  ✓ Editor stopped")
    else:
        print(f"  ✗ Could not stop — try manually:")
        print(f"    pkill -9 -f 'u.editor'    # or: ps aux | grep u.editor → kill -9 <PID>")
    print()
    return 0


def do_status() -> int:
    print(f"\n  ◆ usekit editor Status (port {PORT})")
    print(f"  {'─' * 38}")

    if not _is_listening():
        print(f"  - Editor not running")
    elif _is_our_server():
        print(f"  ✓ Editor running → http://{HOST}:{PORT}")
    else:
        print(f"  ✗ Port {PORT} occupied by a different server")

    print()
    return 0


def do_restart() -> int:
    """Stop (if running) then start. Convenient after applying patches."""
    import time
    print(f"\n  ◆ usekit editor Restart (port {PORT})")
    print(f"  {'─' * 38}")
    if _is_listening():
        if not _is_our_server():
            print(f"  ✗ Port {PORT} occupied by a different process. Aborting.")
            return 1
        # try pid file first, then port scan / ps
        if not _kill_port():
            print(f"  ✗ Could not stop existing editor — try `uk editor stop` manually.")
            return 1
        # Wait for port to free
        for _ in range(20):
            time.sleep(0.1)
            if not _is_listening():
                break
        print(f"  ✓ Old editor stopped")
    return do_start()


# ── Entry ─────────────────────────────────────────────────────────────────────

def run(args: list[str]) -> int:
    """Handle: uk editor stop | uk editor restart | uk editor status"""
    if not args:
        _print_usage()
        return 0

    cmd = args[0].lower()

    if cmd in ("-h", "--help", "help"):
        _print_usage()
        return 0
    elif cmd == "stop":
        return do_stop()
    elif cmd in ("restart", "reload", "-r", "--restart"):
        return do_restart()
    elif cmd in ("status", "stat"):
        return do_status()
    else:
        print(f"[uk editor] Unknown subcommand: '{cmd}'")
        _print_usage()
        return 1


def _print_usage():
    print(f"""uk editor — usekit editor controller

Usage:
    uk editor              start editor (port {PORT})
    uk editor restart      stop + start (use after applying patches)
    uk editor stop         stop editor server
    uk editor status       check if editor is running

Port:
    {PORT}  usekit editor (fixed)""")
