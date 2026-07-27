"""Open USEKIT Editor in Termux with fixed port(7979) and local file saving.

- Fixed port (7979) prevents repeated PWA install prompts (origin changes by port).
- Works when executed via USEKIT exec (u.xpb) where __file__ is NOT defined.
- Starts an in-process HTTP server (thread), no child script required.

Endpoints
  GET  /api/ping
  GET  /api/list?path=/_tmp/   -> {dirs[], files[]}
  GET  /api/read?path=/_tmp/a.txt -> {text}
  POST /api/save   {"storage": "local"|"usekit", ...}
"""

from __future__ import annotations

import json
import socket
import threading
import time
import subprocess
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


# --------- Config ---------
# NOTE:
# - Hard-coded paths removed.
# - USEKIT_BASE and ROOT are resolved at runtime in main() via USEKIT helpers / env overrides.
HOST = "127.0.0.1"
PORT = 7979  # ✅ fixed
PAGE = "index.html"

# Quiet mode: suppress HTTP access logs in Termux
QUIET = True

# Resolved at runtime
USEKIT_BASE: Path | None = None
ROOT: Path | None = None

# Sandbox root — resolved dynamically from file arg in main()
# e.g. main(file="_tmp/scratch.txt")  → USEKIT_SANDBOX_ROOT_REL = "_tmp"
# e.g. main(file="src/base/foo.py")   → USEKIT_SANDBOX_ROOT_REL = "src/base"
USEKIT_SANDBOX_ROOT_REL = ""     # default: USEKIT_BASE 루트 (overridden in main())
USEKIT_SANDBOX_ROOT: Path | None = None
_initial_dir_rel = "_tmp"        # 로드 팝업 초기 폴더 (파일 위치 기준)

# Default file (created if missing)
DEFAULT_FILE = "_tmp/scratch.txt"

BASE_SAVE_DIR: Path | None = None
_BUILTIN_KEY = "__USEKIT_EDITOR_SERVER__"

# ── REPL persistent namespace ──
# Run/Line/Block/Print 계열은 이 ns를 재사용 → 변수 유지
# File tmp(exec)는 매번 새 ns 사용 → 격리
REPL_NS: dict | None = None   # main()에서 초기화

def _init_repl_ns():
    """REPL_NS 초기화 (또는 리셋)"""
    global REPL_NS
    ns: dict = {"__name__": "__main__", "__package__": None,
                "__builtins__": __builtins__}
    try:
        from usekit import u as _u, use as _use
        ns["u"] = _u; ns["use"] = _use
    except Exception:
        try:
            import usekit as _uk
            ns["u"] = ns["use"] = _uk
        except Exception: pass
    try:
        from usekit import uw as _uw; ns["uw"] = _uw
    except Exception: pass
    try:
        from usekit import ut as _ut; ns["ut"] = _ut
    except Exception: pass
    try:
        from usekit import s as _s; ns["s"] = _s
    except Exception: pass
    try:
        from usekit import ua as _ua; ns["ua"] = _ua
    except Exception: pass
    REPL_NS = ns
    return ns


# ── CLI → Python 변환 ──────────────────────────────────────────
# CLI 모드 입력을 Python 코드로 변환.
# 규칙:
#   !cmd           → shell escape (그대로 전달, exec 핸들러의 기존 ! 처리)
#   rjb config     → print(u.rjb(name="config"))
#   wjb config {"a":1} → print(u.wjb(data={"a":1}, name="config"))
#   ljb            → print(u.ljb())
#   ejm {"a":1}    → print(u.ejm(data={"a":1}))
#   xsb "SELECT ..." → print(u.xsb("SELECT ..."))
#   pjb            → print(u.pjb())

# Reuse operation categories from usekit.cli.main
_CLI_NEED_NAME      = {"r", "d", "h"}
_CLI_NEED_NAME_DATA = {"w", "u", "s"}
_CLI_OPTIONAL_NAME  = {"p", "f", "l", "g"}
_CLI_EMIT_OPS       = {"e"}
_CLI_EXEC_OPS       = {"x", "i", "b", "c"}


def _cli_to_python(line: str) -> str:
    """Convert a single CLI line to executable Python code."""
    line = line.strip()
    if not line:
        return ""

    # Shell escape — pass through (exec handler already handles '!')
    if line.startswith("!"):
        return line

    # Multiple lines: convert each
    if "\n" in line:
        return "\n".join(_cli_to_python(l) for l in line.split("\n"))

    parts = line.split(None, 1)  # split into cmd + rest
    cmd = parts[0].lower()

    # -- 특수 키워드 (3글자 아닌 명령) --
    if cmd == "help":
        arg = parts[1].strip() if len(parts) > 1 else ""
        if arg:
            return f'help(u.{arg})'
        return 'u.help()'

    # u-prefix shorthand: urjb -> rjb
    if len(cmd) == 4 and cmd[0] == "u":
        cmd = cmd[1:]

    if len(cmd) != 3:
        # Not a valid CLI command — pass as raw Python
        return line

    op = cmd[0]
    rest = parts[1] if len(parts) > 1 else ""

    # Route by operation type
    if op in _CLI_NEED_NAME_DATA:
        # wjb config {"a":1}  → first token = name, rest = data
        rest_parts = rest.split(None, 1)
        if len(rest_parts) >= 2:
            name, data_str = rest_parts
            return f'print(u.{cmd}(data={data_str}, name="{name}"))'
        elif len(rest_parts) == 1:
            # Only name given, data missing — let it error naturally
            return f'print(u.{cmd}(name="{rest_parts[0]}"))'
        else:
            return f'print(u.{cmd}())'

    elif op in _CLI_NEED_NAME:
        # rjb config  → u.rjb(name="config")
        rest_parts = rest.split(None, 1)
        if rest_parts:
            name = rest_parts[0]
            if len(rest_parts) >= 2:
                return f'print(u.{cmd}(name="{name}", keydata="{rest_parts[1]}"))'
            return f'print(u.{cmd}(name="{name}"))'
        return f'print(u.{cmd}())'

    elif op in _CLI_OPTIONAL_NAME:
        # ljb  → u.ljb()  /  ljb sub  → u.ljb(name="sub")
        if rest.strip():
            return f'print(u.{cmd}(name="{rest.strip()}"))'
        return f'print(u.{cmd}())'

    elif op in _CLI_EMIT_OPS:
        # ejm {"a":1}  → u.ejm(data={"a":1})
        rest_parts = rest.split(None, 1)
        if rest_parts:
            data_str = rest_parts[0]
            if len(rest_parts) >= 2:
                return f'print(u.{cmd}(data={data_str}, type="{rest_parts[1]}"))'
            return f'print(u.{cmd}(data={data_str}))'
        return f'print(u.{cmd}())'

    elif op in _CLI_EXEC_OPS:
        # xsb "SELECT ..."  → u.xsb("SELECT ...")
        if rest.strip():
            return f'print(u.{cmd}("{rest.strip()}"))'
        return f'print(u.{cmd}())'

    else:
        # Unknown op — try as method call anyway
        if rest.strip():
            return f'print(u.{cmd}("{rest.strip()}"))'
        return f'print(u.{cmd}())'


# --------- Helpers ---------
import os


def _find_upwards(start: Path, rel_target: str, max_depth: int = 10) -> Path | None:
    cur = start.resolve()
    for _ in range(max_depth):
        cand = cur / rel_target
        if cand.exists():
            return cand
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def resolve_usekit_base() -> Path:
    """
    Resolve USEKIT base path without hard-coding.

    Priority:
      1) env USEKIT_BASE
      2) usekit helper_const.get_base_path()
      3) usekit.u.pad()
      4) cwd fallback
    """
    env_base = (os.environ.get("USEKIT_BASE") or "").strip()
    if env_base:
        return Path(env_base).expanduser()

    # usekit official base (lazy cached)
    try:
        from usekit.classes.common.utils.helper_const import get_base_path  # type: ignore
        p = get_base_path()
        if p:
            return Path(p)
    except Exception:
        pass

    # compatibility: u.pad()
    try:
        import usekit as u  # type: ignore
        p = u.pad()
        if p:
            return Path(p)
    except Exception:
        pass

    return Path.cwd().resolve()


def resolve_editor_root() -> Path:
    """Resolve editor static root (directory containing index.html).

    IMPORTANT: Editor static assets are packaged inside the USEKIT package.
    Therefore editor_root MUST be resolved from the installed package, not from user base.

    Priority:
      1) importlib.resources (package resource): usekit.tools.editor/index.html
      2) filesystem relative to installed 'usekit' package directory
      3) env USEKIT_EDITOR_ROOT (manual override)
      4) cwd upward search (dev fallback)
    """
    # 1) importlib.resources (preferred)
    try:
        from importlib.resources import files  # py3.9+
        root = files("usekit.tools.editor")
        index = root / "index.html"
        if index.is_file():
            return Path(str(index)).parent
    except Exception:
        pass

    # 2) resolve relative to installed package path
    try:
        import usekit  # type: ignore
        pkg_dir = Path(usekit.__file__).resolve().parent
        cand = (pkg_dir / "tools/editor").resolve()
        if (cand / "index.html").exists():
            return cand
    except Exception:
        pass

    # 3) env override
    env_root = (os.environ.get("USEKIT_EDITOR_ROOT") or "").strip()
    if env_root:
        cand = Path(env_root).expanduser()
        if (cand / "index.html").exists():
            return cand

    # 4) dev fallback: search upwards from cwd
    found = _find_upwards(Path.cwd(), "usekit/tools/editor/index.html")
    if found:
        return found.parent

    raise FileNotFoundError("Cannot resolve editor root (index.html not found in installed package).")

def file_exists_or_raise(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")


def is_listening(host: str, port: int, timeout: float = 0.2) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def wait_listen(host: str, port: int, max_wait: float = 6.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < max_wait:
        if is_listening(host, port):
            return True
        time.sleep(0.08)
    return False


def http_json(url: str, timeout: float = 1.2):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def is_our_server(host: str, port: int) -> bool:
    data = http_json(f"http://{host}:{port}/api/ping")
    return bool(isinstance(data, dict) and data.get("ok") is True)


def safe_token(s: str, default: str = "") -> str:
    if not s:
        return default
    s = s.strip()
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    out = "".join(ch for ch in s if ch in allowed)
    return out or default


def safe_rel_dir(s: str) -> str:
    if not s:
        return ""
    s = s.strip().strip("/").strip("\\")
    parts = []
    for part in s.replace("\\", "/").split("/"):
        tok = safe_token(part)
        if tok in ("", ".", ".."):
            continue
        parts.append(tok)
    return "/".join(parts)


def open_browser(url: str):
    subprocess.Popen(["termux-open-url", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_url(host: str, port: int, page: str, target_file: str,
              initial_data: str | None = None) -> str:
    """에디터 URL 생성. initial_data 있으면 base64 인코딩해서 쿼리에 붙임."""
    url = f"http://{host}:{port}/{page}?file={target_file}"
    if initial_data:
        import base64
        encoded = base64.urlsafe_b64encode(initial_data.encode("utf-8")).decode("ascii")
        url += f"&data={encoded}"
    return url


# --------- Autocomplete cache ---------
_complete_items_cache: list | None = None

def _get_complete_items() -> list:
    global _complete_items_cache
    if _complete_items_cache is not None:
        return _complete_items_cache
    try:
        from usekit import u  # type: ignore
        ops  = u._OPERATIONS   # {r: "read", ...}
        fmts = u._FORMATS      # {j: "json", ...}
        locs = u._LOCATIONS    # {b: "base", ...}
        items = []

        # ── u.xxx 단축형 ──
        for o, od in ops.items():
            for f, fd in fmts.items():
                for l, ld in locs.items():
                    try:
                        getattr(u, o + f + l)
                        items.append({
                            "label":  o + f + l,
                            "detail": f"{od} {fd} {ld}",
                            "kind":   "u",
                        })
                    except AttributeError:
                        pass

        # ── use.xxx 체이닝형 ──
        # 1단계: use.read / use.write / ...
        for o, od in ops.items():
            items.append({
                "label":  od,
                "detail": od,
                "kind":   "use1",
            })

        # 2단계: use.read.json / use.read.txt / ...
        for o, od in ops.items():
            for f, fd in fmts.items():
                # 이 조합이 유효한지 확인 (임의 loc 하나로 체크)
                valid = any(
                    _safe_getattr(u, o + f + l)
                    for l in locs
                )
                if valid:
                    items.append({
                        "label":  f"{od}.{fd}",
                        "detail": f"{od} {fd}",
                        "kind":   "use2",
                    })

        # 3단계: use.read.json.base / ...
        for o, od in ops.items():
            for f, fd in fmts.items():
                for l, ld in locs.items():
                    try:
                        getattr(u, o + f + l)
                        items.append({
                            "label":  f"{od}.{fd}.{ld}",
                            "detail": f"{od} {fd} {ld}",
                            "kind":   "use3",
                        })
                    except AttributeError:
                        pass

        _complete_items_cache = items
    except Exception:
        _complete_items_cache = []
    return _complete_items_cache

def _safe_getattr(obj, name):
    try:
        getattr(obj, name)
        return True
    except AttributeError:
        return False


# --------- HTTP Handler ---------
class EditorHandler(SimpleHTTPRequestHandler):
    # HTTP/1.1 enables chunked transfer encoding, which is required for
    # responses without a Content-Length (like our SSE endpoints). Mobile
    # browsers refuse to start consuming a body without either Content-Length
    # or Transfer-Encoding: chunked.
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    # Dev-friendly: avoid stale JS/CSS/HTML being cached by the browser.
    # This matters even without PWA/ServiceWorker.
    def log_message(self, format, *args):  # noqa: A002
        # Suppress default access logs like:
        # 127.0.0.1 - - [date] "GET /api/list?... HTTP/1.1" 200 -
        if QUIET:
            return
        return super().log_message(format, *args)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _send_json(self, obj: dict, status: int = 200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # --------- USEKIT sandbox helpers ---------
    def _norm_usekit_path(self, raw_path: str, want_dir: bool) -> tuple[Path, str] | None:
        """Normalize and validate a sandbox path.

        Accepts both "/_tmp/..." and "_tmp/..." forms.
        Returns (absolute_path, normalized_client_path_with_leading_slash).
        """
        if raw_path is None:
            raw_path = ""
        p = str(raw_path).strip().replace("\\", "/")
        if p.startswith("/"):
            p = p[1:]
        if p == "":
            p = USEKIT_SANDBOX_ROOT_REL + "/" if USEKIT_SANDBOX_ROOT_REL else ""
        while "//" in p:
            p = p.replace("//", "/")
        # USEKIT_SANDBOX_ROOT_REL="" (루트) 이면 모든 상대경로 허용 (.. 체크는 아래서)
        if USEKIT_SANDBOX_ROOT_REL:
            if not (p == USEKIT_SANDBOX_ROOT_REL or p.startswith(USEKIT_SANDBOX_ROOT_REL + "/")):
                return None
        parts = [x for x in p.split("/") if x]
        if any(x in (".", "..") for x in parts):
            return None

        abs_path = (USEKIT_BASE / p).resolve(strict=False)
        root = USEKIT_SANDBOX_ROOT.resolve(strict=False)
        try:
            abs_path.relative_to(root)
        except Exception:
            return None

        client_path = "/" + "/".join(parts)
        if want_dir and not client_path.endswith("/"):
            client_path += "/"
        if (not want_dir) and client_path.endswith("/"):
            client_path = client_path[:-1]
        return abs_path, client_path

    def do_GET(self):
        # Route on the path component only (strip query string), and match
        # exactly — prefix matching made handler dispatch depend on declaration
        # order (e.g. /api/read vs /api/read_abs).
        from urllib.parse import urlparse as _urlparse
        route = _urlparse(self.path).path
        # sw.js: CACHE_VERSION을 빌드ID로 동적 교체
        if self.path == '/sw.js':
            try:
                sw_path = ROOT / 'sw.js'
                content = sw_path.read_text(encoding='utf-8')
                # __BUILD_ID.txt 읽기
                build_id_path = ROOT / '__BUILD_ID.txt'
                build_id = build_id_path.read_text().strip() if build_id_path.exists() else 'dev'
                # CACHE_VERSION 교체
                import re as _re
                content = _re.sub(
                    r"const CACHE_VERSION = '[^']*'",
                    f"const CACHE_VERSION = 'usekit-editor-{build_id}'",
                    content
                )
                data = content.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                return super().do_GET()
            return
        if route == "/api/ping":
            # Provide base paths so the web editor can pre-bind a default USEKIT save location
            # even before the first save happens.
            self._send_json({
                "ok": True,
                "usekit_base": str(USEKIT_BASE),
                "user_base": str(USEKIT_BASE),
                "base_save_dir": str(BASE_SAVE_DIR),
                "default_usekit_rel_dir": USEKIT_SANDBOX_ROOT_REL,
                "initial_dir": _initial_dir_rel if _initial_dir_rel else "_tmp",
                "default_file": DEFAULT_FILE,
                "editor_root": str(ROOT) if ROOT else "",
            })
            return

        # ── /api/ai_job/* (GET): job control plane ─────────────────────
        # status: GET /api/ai_job/status?id=<job_id>
        # list  : GET /api/ai_job/list?limit=20
        # stream: GET /api/ai_job/stream?id=<job_id>   (SSE, replay+live)
        if route == "/api/ai_job/status":
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            jid = (qs.get("id") or [""])[0]
            if not jid:
                self._send_json({"ok": False, "error": "missing id"}, status=400)
                return
            try:
                from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
                self._send_json(_jb.status(jid))
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        if route == "/api/ai_job/list":
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            try:
                limit = int((qs.get("limit") or ["20"])[0])
            except ValueError:
                limit = 20
            try:
                from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
                self._send_json({"ok": True, "jobs": _jb.list_jobs(limit=limit)})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        if route == "/api/ai_job/stream":
            # SSE: replay history first, then follow live events until done/error.
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            jid = (qs.get("id") or [""])[0]
            if not jid:
                self._send_json({"ok": False, "error": "missing id"}, status=400)
                return
            try:
                from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
            except ImportError as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            # Exact same EOF issue as ai_chat_v2: HTTP/1.1 keep-alive with no
            # Content-Length leaves the request "pending". Close the connection
            # so the client gets a clean end-of-stream.
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            self.close_connection = True

            # CRITICAL: emit a byte IMMEDIATELY so the client recognizes the
            # response has started. Without this, mobile browsers (notably
            # Samsung Internet) keep Response Headers as "Empty" and eventually
            # abort the connection. An SSE comment line is invisible to clients
            # but forces the HTTP layer to flush headers + first body byte.
            try:
                self.wfile.write(b": ping\n\n")
                self.wfile.flush()
            except Exception:
                return

            def _sse(ev):
                try:
                    name = ev.get("event", "msg")
                    msg = f"event: {name}\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                    return True
                except (BrokenPipeError, ConnectionResetError):
                    return False

            try:
                for ev in _jb.stream_events(jid, from_start=True):
                    if not _sse(ev):
                        break
            except Exception as e:
                try:
                    _sse({"event": "error", "error": str(e)})
                except Exception:
                    pass
            finally:
                try:
                    self.wfile.flush()
                except Exception:
                    pass
                try:
                    self.connection.shutdown(socket.SHUT_WR)
                except Exception:
                    pass
            return

        # ── /api/sessions (GET): live session list for the history drawer ──
        #   H2. Returns TWO arrays so the client renders two zones without sorting:
        #     main = real sessions, newest first, no cap (uses ?limit, default 50)
        #     temp = temporary (temp_ prefix, §4.8/4.9 scratch), newest first,
        #            capped at TEMP_CAP so per-turn temp sessions can't flood the list.
        #   list_sessions already returns newest-first; we just split by prefix.
        #   Pull a generous window so main isn't starved by a burst of temp rows.
        if route == "/api/sessions":
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            try:
                limit = int((qs.get("limit") or ["50"])[0])
            except ValueError:
                limit = 50
            TEMP_CAP = 20  # newest 20 temp sessions only (어린왕자: "temp 20쌍이면 충분")
            try:
                from usekit.llm.base.init import lli_db
                # Fetch a wide window so a flood of temp rows can't push main out.
                rows = lli_db.list_sessions(limit=max(limit, 200))

                def _shape(r, is_temp):
                    return {
                        "session_id": r["session_id"],
                        "title": r.get("title") or "",
                        "last_active_at": r.get("last_active_at") or r.get("started_at"),
                        "provider": r.get("provider"),
                        "model": r.get("model"),
                        "turn_count": r.get("turn_count") or 0,
                        "slot": r.get("slot") or "",
                        "is_temp": is_temp,
                    }

                main, temp = [], []
                for r in rows:
                    if str(r["session_id"]).startswith("temp_"):
                        temp.append(_shape(r, True))
                    else:
                        main.append(_shape(r, False))
                main = main[:limit]
                temp = temp[:TEMP_CAP]
                self._send_json({"ok": True, "main": main, "temp": temp})
            except Exception as e:
                self._send_json({"ok": False, "error": f"sessions failed: {e}",
                                 "main": [], "temp": []}, status=500)
            return

        # ── /api/session_turns (GET): ALL turns of one session for card panel ──
        #   H2. View/curation only — uses load_turns_raw (NO restore filter), so
        #   excluded & temporary turns ARE included on purpose (needed by 2단계
        #   toggle). Never reuse this for live restore.
        if route == "/api/session_turns":
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            sid = (qs.get("sid") or [""])[0].strip()
            try:
                limit = int((qs.get("limit") or ["200"])[0])
            except ValueError:
                limit = 200
            if not sid:
                self._send_json({"ok": False, "error": "missing sid",
                                 "turns": []}, status=400)
                return
            try:
                from usekit.llm.base.init import lli_db
                turns = lli_db.load_turns_raw(sid, limit=limit)
                self._send_json({"ok": True, "sid": sid, "turns": turns})
            except Exception as e:
                self._send_json({"ok": False, "error": f"session_turns failed: {e}",
                                 "turns": []}, status=500)
            return

        # ── /api/call_body (GET): one turn's AI-call telemetry + input/output body ──
        # Backs the Memory Editor card [Input]/[Output] view. sid + seq -> TSK_CALL
        # -> log_ref -> JSONL body. has_body=False when telemetry.level=summary.
        if route == "/api/call_body":
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            sid = (qs.get("sid") or [""])[0].strip()
            seq = (qs.get("seq") or [""])[0].strip()
            if not sid or seq == "":
                self._send_json({"ok": False, "error": "missing sid/seq"}, status=400)
                return
            try:
                from usekit.llm.base.init import lli_db
                body = lli_db.load_call_body(sid, seq)
                self._send_json({"ok": True, "sid": sid, "seq": seq, **body})
            except Exception as e:
                self._send_json({"ok": False, "error": f"call_body failed: {e}"}, status=500)
            return

        if route == "/api/ai_meta":
            try:
                from usekit.classes.support.base.init.ai.sbi_ai_meta import all_meta
                self._send_json({"ok": True, "meta": all_meta()})
            except Exception as e:
                self._send_json(
                    {"ok": False, "error": f"ai_meta failed: {e}", "meta": {}},
                    status=500,
                )
            return

        # ── /api/project_meta (GET): read project_meta.md raw text ──
        # Backs the "Project Meta" popup (load current content into editor).
        if route == "/api/project_meta":
            try:
                from usekit.llm.base.init.lli_project_meta import get_project_meta_path
                p = get_project_meta_path()
                text = p.read_text(encoding="utf-8") if p.exists() else ""
                self._send_json({"ok": True, "text": text, "exists": p.exists(),
                                 "path": str(p)})
            except Exception as e:
                self._send_json({"ok": False, "error": f"project_meta read failed: {e}",
                                 "text": ""}, status=500)
            return

        if route == "/api/ai_health":
            try:
                from usekit import us
                from usekit.classes.support.base.init.ai.sbi_ai_meta import all_meta
                out = {}
                for prov, pdata in (all_meta() or {}).get("providers", {}).items():
                    if (pdata or {}).get("enabled") is False:
                        continue
                    h = us.ai.health(prov)
                    out[prov] = {
                        "healthy": h.get("healthy"),
                        "reason": h.get("reason"),
                        "retry_after_ts": h.get("retry_after_ts"),
                        "state": h.get("probe_state"),
                        "tier": pdata.get("tier"),
                        "auth": pdata.get("auth"),
                        "label": pdata.get("label"),
                        "color": pdata.get("color"),
                    }
                self._send_json({"ok": True, "health": out})
            except Exception as e:
                self._send_json({"ok": False, "error": f"health failed: {e}"}, status=500)
            return

        # ── /api/ai_probe (GET): active liveness for ONE provider (token-free) ──
        if route == "/api/ai_probe":
            try:
                from urllib.parse import parse_qs as _pq, urlparse as _up
                from usekit import us
                prov = _pq(_up(self.path).query).get("provider", [""])[0].strip()
                if not prov:
                    self._send_json({"ok": False, "error": "missing_provider"}, status=400)
                    return
                res = us.ai.probe(prov)
                self._send_json({"ok": True, "result": res})
            except Exception as e:
                self._send_json({"ok": False, "error": f"probe failed: {e}"}, status=500)
            return

        # ── /api/ai_probe_all (GET): probe all free providers in one shot ──
        if route == "/api/ai_probe_all":
            try:
                from usekit import us
                results = us.ai.probe_all(only_free=True)
                self._send_json({"ok": True, "results": results})
            except Exception as e:
                self._send_json({"ok": False, "error": f"probe_all failed: {e}"}, status=500)
            return

        # ── /api/ai_key_status (GET): masked key state for api-tier providers ──
        # Never returns raw keys — masked only.
        if route == "/api/ai_key_status":
            try:
                from usekit import us
                from usekit.classes.support.base.init.ai.sbi_ai_meta import all_meta
                out = {}
                for prov, pdata in (all_meta() or {}).get("providers", {}).items():
                    if (pdata or {}).get("auth") != "api_key":
                        continue
                    key_env = (pdata or {}).get("key_env")
                    if not key_env:
                        continue
                    raw = us.key(key_env) or ""
                    out[prov] = {
                        "has_key": bool(raw),
                        "masked": (f"{raw[:4]}...{raw[-4:]}" if len(raw) > 8 else "****") if raw else "(none)",
                        "key_env": key_env,
                    }
                self._send_json({"ok": True, "keys": out})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # ── /api/autostart (GET): check .bashrc autostart status ──
        if route == "/api/autostart":
            try:
                from pathlib import Path as _Path
                bashrc = _Path.home() / '.bashrc'
                enabled = False
                if bashrc.exists():
                    enabled = 'u.editor()' in bashrc.read_text()
                self._send_json({"ok": True, "enabled": enabled})
            except Exception as e:
                self._send_json({"ok": False, "enabled": False, "error": str(e)})
            return

        if route == "/api/read_abs":
            # Absolute path read: /api/read_abs?path=/storage/emulated/0/foo.txt
            try:
                from urllib.parse import urlparse, parse_qs
                from pathlib import Path as _Path
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                raw_path = params.get('path', [''])[0].strip()
                if not raw_path:
                    self._send_json({"ok": False, "error": "missing_path"}, status=400)
                    return
                abs_path = _Path(raw_path).resolve()
                if not abs_path.exists() or not abs_path.is_file():
                    self._send_json({"ok": False, "error": "file_not_found", "path": str(abs_path)}, status=404)
                    return
                text = abs_path.read_text(encoding="utf-8")
                st = abs_path.stat()
                self._send_json({"ok": True, "path": str(abs_path), "text": text, "bytes": len(text.encode("utf-8")), "mtime": int(st.st_mtime * 1000)})
            except Exception as e:
                self._send_json({"ok": False, "error": f"read_abs_failed:{type(e).__name__}", "detail": str(e)}, status=500)
            return

        if route == "/api/read":
            # Sandbox read: /api/read?path=/_tmp/usekit/filename.txt
            # Uses _norm_usekit_path for security (stays within USEKIT_SANDBOX_ROOT)
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                raw_path = params.get('path', [''])[0]
                if not raw_path:
                    self._send_json({"ok": False, "error": "missing_path"}, status=400)
                    return
                norm = self._norm_usekit_path(raw_path, want_dir=False)
                if not norm:
                    self._send_json({"ok": False, "error": "invalid_path"}, status=400)
                    return
                abs_path, client_path = norm
                if not abs_path.exists() or not abs_path.is_file():
                    self._send_json({"ok": False, "error": "file_not_found", "path": client_path}, status=404)
                    return
                text = abs_path.read_text(encoding="utf-8")
                st   = abs_path.stat()
                self._send_json({
                    "ok":    True,
                    "path":  client_path,
                    "text":  text,
                    "bytes": len(text.encode("utf-8")),
                    "mtime": int(st.st_mtime * 1000),
                })
            except Exception as e:
                self._send_json({"ok": False, "error": f"read_failed:{type(e).__name__}", "detail": str(e)}, status=500)
            return

        if route == "/api/load":
            # Legacy load: /api/load?path=usekit/tools/editor.js  (relative to USEKIT_BASE)
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                rel_path = params.get('path', [''])[0]
                
                if not rel_path:
                    self._send_json({"ok": False, "error": "missing_path"}, status=400)
                    return
                
                full_path = USEKIT_BASE / rel_path
                
                if not full_path.exists() or not full_path.is_file():
                    self._send_json({"ok": False, "error": "file_not_found", "path": str(full_path)}, status=404)
                    return
                
                text = full_path.read_text(encoding="utf-8")
                st   = full_path.stat()
                self._send_json({
                    "ok":    True,
                    "path":  str(full_path),
                    "text":  text,
                    "bytes": len(text.encode("utf-8")),
                    "mtime": int(st.st_mtime * 1000),
                })
            except Exception as e:
                self._send_json({"ok": False, "error": f"load_failed:{type(e).__name__}", "detail": str(e)}, status=500)
            return
        
        
        if route == "/api/list_abs":
            # Absolute path list: /api/list_abs?path=/storage/emulated/0/
            try:
                from urllib.parse import urlparse, parse_qs
                from pathlib import Path as _Path
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                raw_path = params.get('path', ['/'])[0].strip()
                if not raw_path:
                    raw_path = '/'
                abs_dir = _Path(raw_path).resolve()
                if not abs_dir.exists() or not abs_dir.is_dir():
                    self._send_json({"ok": False, "error": "dir_not_found", "path": str(abs_dir)}, status=404)
                    return
                dirs: list[str] = []
                file_metas: list[dict] = []
                for item in abs_dir.iterdir():
                    if item.name.startswith('.'):
                        continue
                    if item.is_dir():
                        dirs.append(item.name + "/")
                    elif item.is_file():
                        try:
                            st = item.stat()
                            file_metas.append({"name": item.name, "size": st.st_size, "mtime": int(st.st_mtime * 1000)})
                        except Exception:
                            file_metas.append({"name": item.name, "size": 0, "mtime": 0})
                dirs.sort(key=lambda x: x.lower())
                file_metas.sort(key=lambda x: x["name"].lower())
                files = [m["name"] for m in file_metas]
                self._send_json({"ok": True, "path": str(abs_dir) + "/", "dirs": dirs, "files": files, "file_metas": file_metas})
            except Exception as e:
                self._send_json({"ok": False, "error": f"list_abs_failed:{type(e).__name__}", "detail": str(e)}, status=500)
            return

        if route == "/api/list":
            # Sandbox list (preferred): /api/list?path=/_tmp/usekit/
            # Legacy list: /api/list?dir=usekit/tools
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)

                raw_path = params.get('path', [''])[0]
                if raw_path:
                    norm = self._norm_usekit_path(raw_path, want_dir=True)
                    if not norm:
                        self._send_json({"ok": False, "error": "invalid_path"}, status=400)
                        return
                    abs_dir, client_dir = norm
                    if not abs_dir.exists() or not abs_dir.is_dir():
                        self._send_json({"ok": False, "error": "dir_not_found", "path": client_dir}, status=404)
                        return

                    dirs: list[str] = []
                    file_metas: list[dict] = []
                    for item in abs_dir.iterdir():
                        if item.name.startswith('.'):
                            continue
                        if item.is_dir():
                            dirs.append(item.name + "/")
                        elif item.is_file():
                            try:
                                st = item.stat()
                                file_metas.append({
                                    "name": item.name,
                                    "size": st.st_size,
                                    "mtime": int(st.st_mtime * 1000),  # ms
                                })
                            except Exception:
                                file_metas.append({"name": item.name, "size": 0, "mtime": 0})

                    dirs.sort(key=lambda x: x.lower())
                    file_metas.sort(key=lambda x: x["name"].lower())
                    # 하위호환: files 문자열 배열도 유지
                    files = [m["name"] for m in file_metas]

                    self._send_json({
                        "ok": True,
                        "path": client_dir,
                        "dirs": dirs,
                        "files": files,
                        "file_metas": file_metas,
                    })
                    return

                # ----- legacy mode -----
                rel_dir = params.get('dir', [''])[0]
                base_dir = USEKIT_BASE / rel_dir if rel_dir else USEKIT_BASE

                if not base_dir.exists() or not base_dir.is_dir():
                    self._send_json({"ok": False, "error": "dir_not_found"}, status=404)
                    return

                items = []
                for item in sorted(base_dir.iterdir()):
                    if item.name.startswith('.'):
                        continue
                    rel = item.relative_to(USEKIT_BASE)
                    items.append({
                        "name": item.name,
                        "path": str(rel),
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0
                    })

                self._send_json({
                    "ok": True,
                    "dir": str(base_dir.relative_to(USEKIT_BASE)) if base_dir != USEKIT_BASE else "",
                    "items": items
                })
            except Exception as e:
                self._send_json({"ok": False, "error": f"list_failed:{type(e).__name__}", "detail": str(e)}, status=500)
            return

        if route == "/api/complete":
            self._send_json({"ok": True, "items": _get_complete_items()})
            return

        return super().do_GET()


    def do_DELETE(self):
        from urllib.parse import urlparse as _urlparse
        route = _urlparse(self.path).path

        # ── DELETE /api/session?sid=..&current_slot_sid=.. ──
        #   Session manager (left panel) is the ONLY place that deletes a session
        #   (§ SESSION_ID_MANAGEMENT). 409 guard: if the session is the one the
        #   current slot is bound to, refuse — deleting it would feel like data
        #   loss (slot transcript would dangle). Client must open another session
        #   or reset the slot first. No force-delete / auto-clear in MVP.
        if route == "/api/session":
            try:
                from urllib.parse import urlparse, parse_qs
                params = parse_qs(urlparse(self.path).query)
                sid = (params.get("sid") or [""])[0].strip()
                current = (params.get("current_slot_sid") or [""])[0].strip()
                if not sid:
                    self._send_json({"ok": False, "error": "missing sid"}, status=400)
                    return
                if current and sid == current:
                    self._send_json({
                        "ok": False,
                        "reason": "session_in_use_by_current_slot",
                        "message": "현재 슬롯에서 사용 중인 세션입니다. 다른 세션을 먼저 여세요.",
                    }, status=409)
                    return
                from usekit.llm.base.init import lli_db
                result = lli_db.delete_session(sid)
                self._send_json({"ok": True, **result})
            except Exception as e:
                self._send_json({"ok": False,
                                 "error": f"delete_session_failed:{type(e).__name__}",
                                 "detail": str(e)}, status=500)
            return

        if route == "/api/delete":
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                raw_path = params.get('path', [''])[0]
                if not raw_path:
                    self._send_json({"ok": False, "error": "missing_path"}, status=400)
                    return
                norm = self._norm_usekit_path(raw_path, want_dir=False)
                if not norm:
                    self._send_json({"ok": False, "error": "invalid_path"}, status=400)
                    return
                abs_path, client_path = norm
                if not abs_path.exists():
                    self._send_json({"ok": False, "error": "file_not_found"}, status=404)
                    return
                if not abs_path.is_file():
                    self._send_json({"ok": False, "error": "not_a_file"}, status=400)
                    return
                abs_path.unlink()
                self._send_json({"ok": True, "path": client_path})
            except Exception as e:
                self._send_json({"ok": False, "error": f"delete_failed:{type(e).__name__}", "detail": str(e)}, status=500)
        else:
            self._send_json({"ok": False, "error": "not_found"}, status=404)

    def do_POST(self):
        # Exact-match routing on the path component (see do_GET).
        from urllib.parse import urlparse as _urlparse
        route = _urlparse(self.path).path
        # ── /api/autostart (POST): toggle .bashrc autostart ──
        if route == "/api/autostart":
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n).decode("utf-8"))
                enable = bool(payload.get("enable", False))
                from usekit.classes.common.init.helper_termux_storage import _register_editor_autostart
                _register_editor_autostart(enable=enable, verbose=False)
                self._send_json({"ok": True, "enabled": enable})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)})
            return

        # ── /api/ai_key (POST): save/clear an API key into .env via us.key ──
        # Validates against key_pattern from sys_ai.yaml. Adapter reads key_env first.
        # Raw keys are never logged or echoed — only a masked form is returned.
        if route == "/api/ai_key":
            try:
                import re as _re
                from usekit import us
                from usekit.classes.support.base.init.ai.sbi_ai_meta import all_meta
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                prov = (body.get("provider") or "").lower().strip()
                key = body.get("key")  # None or "" → clear
                if not prov:
                    self._send_json({"ok": False, "error": "missing_provider"}, status=400)
                    return
                meta = (all_meta() or {}).get("providers", {}).get(prov, {})
                key_env = meta.get("key_env")
                if not key_env:
                    self._send_json({"ok": False, "error": f"{prov} is not key-gated"}, status=400)
                    return
                if not key:
                    us.delkey(key_env)
                    self._send_json({"ok": True, "cleared": True, "masked": "(none)"})
                    return
                pat = meta.get("key_pattern")
                if pat and not _re.search(pat, key):
                    self._send_json({"ok": False, "error": f"key does not match {pat}"}, status=400)
                    return
                us.key(key_env, key)
                masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
                self._send_json({"ok": True, "saved": True, "masked": masked})
            except Exception as e:
                self._send_json({"ok": False, "error": f"ai_key failed: {e}"}, status=500)
            return

        # ── /api/project_meta (POST): write project_meta.md, or reset to default ──
        # body: {"text": "...full md..."}  → save
        #       {"reset": true}            → restore built-in default template
        if route == "/api/project_meta":
            try:
                from usekit.llm.base.init.lli_project_meta import get_project_meta_path
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                p = get_project_meta_path()
                p.parent.mkdir(parents=True, exist_ok=True)
                if body.get("reset"):
                    # Reset baseline = the immutable default sibling file
                    # (project_meta.default.md), never touched by auto-save.
                    # If missing (older installs), generate the built-in and seed
                    # the default file so future resets read from it.
                    from usekit.llm.base.init.lli_project_meta import (
                        get_project_meta_default_path,
                    )
                    dp = get_project_meta_default_path()
                    try:
                        text = dp.read_text(encoding="utf-8")
                    except Exception:
                        try:
                            from usekit.classes.common.setup.helper_setup_config import (
                                _generate_project_meta_md,
                            )
                            text = _generate_project_meta_md()
                        except Exception:
                            text = ""
                        try:
                            dp.parent.mkdir(parents=True, exist_ok=True)
                            dp.write_text(text, encoding="utf-8")
                        except Exception:
                            pass
                    p.write_text(text, encoding="utf-8")
                    self._send_json({"ok": True, "reset": True, "text": text})
                    return
                if body.get("snapshot"):
                    # Save: copy the working copy → last snapshot (project_meta.last.md).
                    from usekit.llm.base.init.lli_project_meta import (
                        get_project_meta_last_path,
                    )
                    lp = get_project_meta_last_path()
                    try:
                        cur = p.read_text(encoding="utf-8")
                    except Exception:
                        cur = ""
                    lp.parent.mkdir(parents=True, exist_ok=True)
                    lp.write_text(cur, encoding="utf-8")
                    self._send_json({"ok": True, "snapshot": True})
                    return
                if body.get("restore"):
                    # Load: restore the last snapshot → working copy.
                    from usekit.llm.base.init.lli_project_meta import (
                        get_project_meta_last_path,
                    )
                    lp = get_project_meta_last_path()
                    try:
                        text = lp.read_text(encoding="utf-8")
                    except Exception:
                        self._send_json({"ok": False, "error": "no_snapshot"})
                        return
                    p.write_text(text, encoding="utf-8")
                    self._send_json({"ok": True, "restore": True, "text": text})
                    return
                text = body.get("text")
                if text is None:
                    self._send_json({"ok": False, "error": "missing_text"}, status=400)
                    return
                p.write_text(text, encoding="utf-8")
                self._send_json({"ok": True, "saved": True})
            except Exception as e:
                self._send_json({"ok": False, "error": f"project_meta write failed: {e}"},
                                status=500)
            return

        # ── /api/exec: 현재 Python 프로세스에서 코드 실행 ──────────────
        if route == "/api/exec":
            import io, contextlib, threading, traceback
            try:
                length  = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                code    = str(payload.get("code", ""))
                mode    = str(payload.get("mode", "exec"))
                # mode: "exec"       — 기본 exec (RUN 전체, File tmp 래핑)
                #       "single"     — REPL 스타일, 표현식 결과 자동표시 (Line Run)
                #       "block_echo" — exec + 마지막 표현식 echo (Block, Selection, Run Print)
                # Timeout cap: 120s for AI commands / external requests, 30s otherwise
                _ai_timeout = 120
                _exec_timeout_cap = 30
                _code_preview = str(payload.get("code", "")).lstrip()

                # Detect external network calls (requests, urllib, http.client, etc.)
                _has_network = any(kw in code for kw in (
                    "requests.", "urllib.request", "http.client",
                    "httpx.", "aiohttp.", "urlopen(",
                    "ua.chat(", "ua.ask(", "ua.run(", "ua.send(",
                    "us.ai.call", "us.ai.serve", ".ai.call(",
                    "us.ai.call_stream", "dispatch_one", "gateway.call",
                ))
                _is_ai_cmd = _code_preview.startswith(("!uk ai ", "!usekit ai "))
                # Also treat in-code gateway/LLM calls as AI work (they spawn
                # CLI subprocesses / network calls that exceed the exec cap).
                if not _is_ai_cmd:
                    _ai_markers = ("us.ai.call", "us.ai.serve", "us.ai.call_stream",
                                   "ua.run", "ua.chat", "ua.send",
                                   ".ai.call", "dispatch_one", "gateway.call")
                    _is_ai_cmd = any(m in _code_preview for m in _ai_markers)

                if _is_ai_cmd or _has_network:
                    # Network/AI calls: ignore client's short timeout, use extended cap
                    timeout = _ai_timeout
                else:
                    timeout = min(int(payload.get("timeout", 10)), _exec_timeout_cap)

                inputs  = list(payload.get("inputs", []))

                # REPL 계열은 persistent ns, exec(File tmp)는 매번 새 ns
                if mode in ("single", "block_echo", "live", "cli"):
                    if REPL_NS is None:
                        _init_repl_ns()
                    ns = REPL_NS
                else:
                    # exec 모드: 격리된 새 ns
                    ns = {"__name__": "__main__", "__builtins__": __builtins__}
                    try:
                        from usekit import u as _u, use as _use
                        ns["u"] = _u; ns["use"] = _use
                    except Exception:
                        try:
                            import usekit as _uk
                            ns["u"] = ns["use"] = _uk
                        except Exception: pass
                    try:
                        from usekit import uw as _uw; ns["uw"] = _uw
                    except Exception: pass
                    try:
                        from usekit import ut as _ut; ns["ut"] = _ut
                    except Exception: pass
                    try:
                        from usekit import s as _s; ns["s"] = _s
                    except Exception: pass
                    try:
                        from usekit import ua as _ua; ns["ua"] = _ua
                    except Exception: pass

                # input() 가로채기
                _input_queue = list(inputs)
                def _fake_input(prompt=''):
                    stdout_buf.write(str(prompt))
                    if _input_queue:
                        val = _input_queue.pop(0)
                        stdout_buf.write(val + '\n')
                        return val
                    return ''

                stdout_buf = io.StringIO()
                stderr_buf = io.StringIO()
                exc_info   = [None]

                ns["input"] = _fake_input

                def _run():
                    try:
                        with contextlib.redirect_stdout(stdout_buf), \
                             contextlib.redirect_stderr(stderr_buf):

                            # Shell escape: lines starting with '!' run as shell commands
                            if code.lstrip().startswith("!"):
                                import subprocess as _sp
                                _shell_cmd = code.lstrip()[1:].strip()
                                if _shell_cmd:
                                    # AI 명령은 timeout 확장
                                    _shell_timeout = _ai_timeout if _shell_cmd.startswith(("uk ai ", "usekit ai ")) else 30
                                    _r = _sp.run(
                                        _shell_cmd, shell=True,
                                        capture_output=True, text=True,
                                        timeout=_shell_timeout,
                                    )
                                    if _r.stdout:
                                        print(_r.stdout, end="")
                                    if _r.stderr:
                                        print(_r.stderr, end="")

                            elif mode == "cli":
                                # CLI 모드: 3글자 명령 → Python 변환 후 exec
                                _py_code = _cli_to_python(code)
                                exec(compile(_py_code, "<USEKIT-CLI>", "exec"), ns)

                            elif mode == "single":
                                # REPL 스타일: compile(..., "single") → 표현식 결과 자동 표시
                                exec(compile(code, "<USEKIT-REPL>", "single"), ns)

                            elif mode == "live":
                                # Live: REPL_NS에서 전체 파일 exec + 마지막 표현식 echo
                                import ast as _ast_l
                                _tree_l = _ast_l.parse(code, mode="exec")
                                if _tree_l.body and isinstance(_tree_l.body[-1], _ast_l.Expr):
                                    last_expr_l = _tree_l.body.pop()
                                    body_l = _ast_l.Module(body=_tree_l.body, type_ignores=[])
                                    expr_l = _ast_l.Expression(last_expr_l.value)
                                    _ast_l.fix_missing_locations(body_l)
                                    _ast_l.fix_missing_locations(expr_l)
                                    if body_l.body:
                                        exec(compile(body_l, "<USEKIT-LIVE>", "exec"), ns)
                                    _result = eval(compile(expr_l, "<USEKIT-LIVE>", "eval"), ns)
                                    if _result is not None:
                                        if isinstance(_result, (dict, list, tuple, set, frozenset)):
                                            import pprint as _pp_l
                                            _pp_l.pprint(_result, stream=stdout_buf, width=72)
                                        else:
                                            print(_result)
                                else:
                                    exec(compile(_tree_l, "<USEKIT-LIVE>", "exec"), ns)

                            elif mode == "block_echo":
                                # exec + 마지막 표현식 echo
                                import ast as _ast
                                _tree = _ast.parse(code, mode="exec")
                                if _tree.body and isinstance(_tree.body[-1], _ast.Expr):
                                    last_expr = _tree.body.pop()
                                    body_mod = _ast.Module(body=_tree.body, type_ignores=[])
                                    expr_mod = _ast.Expression(last_expr.value)
                                    _ast.fix_missing_locations(body_mod)
                                    _ast.fix_missing_locations(expr_mod)
                                    if body_mod.body:
                                        exec(compile(body_mod, "<USEKIT-BLOCK>", "exec"), ns)
                                    _result = eval(compile(expr_mod, "<USEKIT-BLOCK>", "eval"), ns)
                                    if _result is not None:
                                        if isinstance(_result, (dict, list, tuple, set, frozenset)):
                                            import pprint as _pp
                                            _pp.pprint(_result, stream=stdout_buf, width=72)
                                        else:
                                            print(_result)
                                else:
                                    exec(compile(_tree, "<USEKIT-BLOCK>", "exec"), ns)

                            else:
                                # 기본 exec 모드
                                exec(compile(code, "<editor>", "exec"), ns)

                    except Exception:
                        exc_info[0] = traceback.format_exc()

                th = threading.Thread(target=_run, daemon=True)
                th.start()
                th.join(timeout)

                if th.is_alive():
                    self._send_json({"ok": False,
                                     "error": f"timeout after {timeout}s",
                                     "stdout": stdout_buf.getvalue(),
                                     "stderr": stderr_buf.getvalue()})
                    return

                self._send_json({
                    "ok":    exc_info[0] is None,
                    "stdout": stdout_buf.getvalue(),
                    "stderr": stderr_buf.getvalue(),
                    "error":  exc_info[0] or "",
                })
            except Exception as e:
                self._send_json({"ok": False, "error": f"exec_failed:{e}"}, status=500)
            return

        # ── /api/reset_repl: REPL 네임스페이스 초기화 ──────────────
        if route == "/api/reset_repl":
            _init_repl_ns()
            self._send_json({"ok": True, "message": "REPL namespace reset"})
            return

        # ── /api/reload_usekit: usekit module cache clear + reimport ──
        if route == "/api/reload_usekit":
            import sys as _sys
            try:
                # clear all usekit modules from cache
                _removed = [k for k in _sys.modules if k.startswith("usekit")]
                for k in _removed:
                    del _sys.modules[k]

                # reimport core
                import usekit
                from usekit import u, use, uw, ut, s

                # reimport ua if available
                _has_ua = False
                try:
                    from usekit import ua
                    _has_ua = True
                except Exception:
                    pass

                # reset REPL ns too
                _init_repl_ns()

                _msg = f"✓ usekit reloaded ({len(_removed)} modules)"
                if _has_ua:
                    _msg += " + ua"
                self._send_json({"ok": True, "message": _msg})
            except Exception as e:
                self._send_json({"ok": False, "error": f"reload failed: {e}"})
            return

        # ── /api/ai_job/*: long-running jobs (deep work, decoupled HTTP) ──
        # start  : POST {prompt, provider?, model?, session?} → {job_id}
        # status : GET  ?id=<job_id>                          → meta snapshot
        # list   : GET  ?limit=20                             → recent jobs
        # cancel : POST {id}                                  → terminate
        # stream : GET  ?id=<job_id>                          → SSE (replay+live)
        if route == "/api/ai_job/start":
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            except Exception as e:
                self._send_json({"ok": False, "error": f"bad request: {e}"}, status=400)
                return
            prompt = (payload.get("prompt") or "").strip()
            if not prompt:
                self._send_json({"ok": False, "error": "empty prompt"}, status=400)
                return
            try:
                from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
                r = _jb.start(
                    prompt,
                    provider=payload.get("provider", "claude"),
                    model=payload.get("model"),
                    session=payload.get("session"),
                )
                self._send_json(r)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        if route == "/api/ai_job/cancel":
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            except Exception:
                payload = {}
            jid = payload.get("id") or payload.get("job_id")
            if not jid:
                self._send_json({"ok": False, "error": "missing id"}, status=400)
                return
            try:
                from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
                self._send_json(_jb.cancel(jid))
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # ── /api/ai_chat_v2: SSE streaming via ua.chat() pipeline ────────
        # Uses serve_chat_v2 generator — streams stage progress + final result.
        # Body: {"provider", "prompt", "mode", "worker", "workers", "quality",
        #        "model", "input_text", "input_paths", "recirculate", "max_rounds",
        #        "config", "timeout", "max_tokens", "temperature"}
        # SSE events: status(stage progress), done(final), error
        if route == "/api/ai_chat_v2":
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception as e:
                self._send_json({"ok": False, "error": f"bad request: {e}"}, status=400)
                return

            provider = str(payload.get("provider", "")).strip()
            prompt   = str(payload.get("prompt", ""))
            if not provider or not prompt.strip():
                self._send_json({"ok": False, "error": "missing provider or prompt"}, status=400)
                return

            # The panel sends max_tokens / temperature at the TOP LEVEL of the
            # body, but only `config` is forwarded into conn_kwargs (ua.conn).
            # Without this merge the UI's MAX TOKENS selector and temperature
            # never reach the adapter (config.get("max_tokens"/"temperature")).
            # Fold them in here; an explicit value inside `config` still wins.
            _cfg = payload.get("config")
            if not isinstance(_cfg, dict):
                _cfg = {}
            if payload.get("max_tokens") is not None and "max_tokens" not in _cfg:
                try:
                    _cfg["max_tokens"] = int(payload["max_tokens"])
                except (TypeError, ValueError):
                    pass
            if payload.get("temperature") is not None and "temperature" not in _cfg:
                try:
                    _cfg["temperature"] = float(payload["temperature"])
                except (TypeError, ValueError):
                    pass
            payload["config"] = _cfg

            # SSE headers.
            # NOTE: With protocol_version="HTTP/1.1" and no Content-Length,
            # the client can only detect end-of-response via a chunked
            # terminator or a socket close. We send "Connection: close" and
            # explicitly close the connection at the end so the request
            # actually finishes (otherwise it stays "pending" forever even
            # though the chat content already rendered).
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            # Stop keep-alive: this handler owns the socket until close.
            self.close_connection = True

            def _sse(event, data):
                try:
                    msg = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass

            _sse("status", {"type": "connected", "provider": provider})

            try:
                from usekit.classes.support.base.init.ai.sbi_ai_chat import serve_chat_v2

                gen = serve_chat_v2(
                    provider=provider,
                    prompt=prompt,
                    mode=payload.get("mode", "auto"),
                    worker=payload.get("worker"),
                    workers=int(payload.get("workers", 3)),
                    quality=payload.get("quality", "auto"),
                    model=payload.get("model") or None,
                    config=payload.get("config") or {},
                    input_text=payload.get("input_text", ""),
                    input_paths=payload.get("input_paths") or [],
                    images=payload.get("images") or [],
                    search=bool(payload.get("search", False)),
                    recirculate=payload.get("recirculate", True),
                    max_rounds=int(payload.get("max_rounds", 2)),
                    timeout=int(payload.get("timeout", 120)),
                    continue_=bool(payload.get("continue", False)),
                    client_session_id=str(payload.get("session_id", "") or ""),
                    slot=str(payload.get("slot", "") or ""),
                )

                for chunk in gen:
                    evt = chunk.pop("event", "status")
                    _sse(evt, chunk)
            except Exception as e:
                _sse("error", {"error": f"v2 stream failed: {e}"})
            finally:
                # Flush any buffered bytes and shut down the write side so the
                # client receives EOF and the request leaves "pending" state.
                try:
                    self.wfile.flush()
                except Exception:
                    pass
                try:
                    self.connection.shutdown(socket.SHUT_WR)
                except Exception:
                    pass
            return

        # ── /api/ai_stream: SSE streaming AI response ──────────────────
        # Same payload as /api/ai_chat but returns text/event-stream.
        # Each SSE event: "event: <type>\ndata: <json>\n\n"
        # Events: status, delta, tool, done, error
        if route == "/api/ai_stream":
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception as e:
                self._send_json({"ok": False, "error": f"bad request: {e}"}, status=400)
                return

            provider = str(payload.get("provider", "")).strip()
            prompt   = str(payload.get("prompt", ""))
            model    = payload.get("model") or None
            config   = payload.get("config") or {}
            timeout  = int(payload.get("timeout", 300))

            if not provider or not prompt.strip():
                self._send_json({"ok": False, "error": "missing provider or prompt"}, status=400)
                return

            # Pre-check: is this a CLI provider? Import early so it doesn't block after headers.
            _is_cli = False
            _stream_gen = None
            try:
                from usekit.classes.support.base.init.ai.sbi_ai_meta import is_cli
                _prov = provider.lower().strip()
                if _prov == "claude":
                    _prov = "claude_code"
                _is_cli = is_cli(_prov)
            except ImportError:
                _is_cli = provider.lower().strip() in ("claude", "claude_code")

            if _is_cli:
                from usekit.classes.support.base.init.ai.sbi_ai_chat import stream_cli
                # Pre-create generator (doesn't run until first next())
                _stream_gen = stream_cli(
                    provider=provider,
                    prompt=prompt,
                    model=model,
                    config=config if isinstance(config, dict) else {},
                    timeout=timeout,
                )

            # SSE headers — send immediately.
            # See ai_chat_v2 above: HTTP/1.1 with no Content-Length needs an
            # explicit close to deliver EOF, otherwise the request stays
            # "pending" in DevTools after the stream content arrives.
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            self.close_connection = True

            def _sse(event, data):
                try:
                    msg = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass

            # Immediate heartbeat so client knows connection is alive
            _sse("status", {"type": "connected", "provider": provider})

            try:
                if _is_cli and _stream_gen:
                    for chunk in _stream_gen:
                        evt = chunk.pop("event", "delta")
                        _sse(evt, chunk)
                else:
                    # Non-CLI providers: fall back to blocking call + single SSE
                    _sse("status", {"type": "start", "provider": provider})
                    from usekit import us
                    result = us.ai.serve_chat(
                        provider=provider,
                        prompt=prompt,
                        model=model,
                        config=config if isinstance(config, dict) else {},
                        timeout=timeout,
                    )
                    if result.get("ok"):
                        _sse("delta", {"text": result.get("text", "")})
                        _sse("done", result)
                    else:
                        _sse("error", {"error": result.get("error", "unknown")})
            except Exception as e:
                _sse("error", {"error": f"stream failed: {e}"})
            finally:
                try:
                    self.wfile.flush()
                except Exception:
                    pass
                try:
                    self.connection.shutdown(socket.SHUT_WR)
                except Exception:
                    pass
            return

        # ── /api/ai_chat: provider-agnostic AI chat dispatch ──────
        # Body: {"provider": "qwen"|"gemini"|"ollama"|"claude"|...,
        #        "prompt":   "...",
        #        "model":    "..." (optional),
        #        "config":   {...} (optional per-call overrides),
        #        "timeout":  120 (optional, seconds)}
        # Returns: {"ok": bool, "text": str, "error": str|None,
        #           "provider": str, "model": str, "elapsed": float}
        if route == "/api/ai_chat":
            try:
                n = int(self.headers.get("Content-Length") or "0")
                raw = self.rfile.read(n) if n > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8") or "{}")
            except Exception as e:
                self._send_json(
                    {"ok": False, "error": f"bad request: {e}",
                     "text": "", "provider": "", "model": "", "elapsed": 0},
                    status=400,
                )
                return

            provider = str(payload.get("provider", "")).strip()
            prompt   = str(payload.get("prompt", ""))
            model    = payload.get("model") or None
            config   = payload.get("config") or {}
            timeout  = int(payload.get("timeout") or 120)

            if not provider:
                self._send_json(
                    {"ok": False, "error": "missing provider",
                     "text": "", "provider": "", "model": "", "elapsed": 0},
                    status=400,
                )
                return
            if not prompt.strip():
                self._send_json(
                    {"ok": False, "error": "missing prompt",
                     "text": "", "provider": provider, "model": model or "", "elapsed": 0},
                    status=400,
                )
                return

            try:
                # use_pipeline: true → serve_chat_full (ua.chat pipeline)
                # use_pipeline: false/missing → serve_chat (ua.run, legacy)
                use_pipeline = payload.get("use_pipeline", False)

                if use_pipeline:
                    from usekit.classes.support.base.init.ai.sbi_ai_chat import serve_chat_full
                    result = serve_chat_full(
                        provider=provider,
                        prompt=prompt,
                        mode=payload.get("mode", "auto"),
                        worker=payload.get("worker"),
                        workers=int(payload.get("workers", 3)),
                        quality=payload.get("quality", "auto"),
                        model=model,
                        config=config if isinstance(config, dict) else {},
                        input_text=payload.get("input_text", ""),
                        input_paths=payload.get("input_paths") or [],
                        recirculate=payload.get("recirculate", True),
                        max_rounds=int(payload.get("max_rounds", 2)),
                        timeout=timeout,
                    )
                else:
                    from usekit import us
                    result = us.ai.serve_chat(
                        provider=provider,
                        prompt=prompt,
                        model=model,
                        config=config if isinstance(config, dict) else {},
                        timeout=timeout,
                    )
                # serve_chat never raises; status reflects ok flag.
                status = 200 if result.get("ok") else 502
                self._send_json(result, status=status)
            except Exception as e:
                self._send_json(
                    {"ok": False, "error": f"serve_chat crashed: {e}",
                     "text": "", "provider": provider, "model": model or "",
                     "elapsed": 0},
                    status=500,
                )
            return

        # ── /api/tts: text → speech (Gemini TTS, cached WAV) ─────────────
        #   Proving ground for SRSNote character voice. Returns raw audio/wav.
        #   Disk acts only as a cache: identical (model|voice|text) is never
        #   re-synthesized (saves cost + garbage). Cache is self-GC'd.
        if route == "/api/tts":
            import base64 as _b64, hashlib as _hl
            try:
                n = int(self.headers.get("Content-Length") or "0")
                payload = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            except Exception as e:
                self._send_json({"ok": False, "error": f"bad request: {e}"}, status=400)
                return

            text = (payload.get("text") or "").strip()
            voice = payload.get("voice") or "Kore"
            provider = payload.get("provider") or "gemini"
            tts_model = payload.get("tts_model") or "gemini-2.5-flash-preview-tts"
            if not text:
                self._send_json({"ok": False, "error": "empty text"}, status=400)
                return

            tts_dir = os.path.join(os.path.expanduser("~"), ".usekit_tts_cache")
            os.makedirs(tts_dir, exist_ok=True)
            digest = _hl.sha256(f"{tts_model}|{voice}|{text}".encode("utf-8")).hexdigest()[:32]
            cache_path = os.path.join(tts_dir, f"tts_{digest}.wav")

            wav_bytes = None
            if os.path.isfile(cache_path):
                try:
                    with open(cache_path, "rb") as f:
                        wav_bytes = f.read()
                except OSError:
                    wav_bytes = None

            if wav_bytes is None:
                # Resolve api key (mirror serve_chat layering: yaml key_env -> env,
                # then user-stored provider config overrides).
                try:
                    from usekit.classes.support.base.init.ai.sbi_ai_meta import providers as _mp
                    from usekit.classes.support.base.init.ai.sbi_ai_config import get_provider
                    api_key = ""
                    _ym = _mp().get(provider) or {}
                    _kenv = _ym.get("key_env")
                    if _kenv and os.environ.get(_kenv):
                        api_key = os.environ[_kenv]
                    _stored = get_provider(provider) or {}
                    if _stored.get("api_key"):
                        api_key = _stored["api_key"]
                except Exception as e:
                    self._send_json({"ok": False, "error": f"key resolve: {e}"}, status=500)
                    return
                if not api_key:
                    self._send_json({"ok": False, "error": "no api key for provider"}, status=400)
                    return

                from usekit.llm.provider.prov_gemini import ProvGemini
                res = ProvGemini().synthesize(text, {
                    "mode": "rest", "api_key": api_key,
                    "tts_model": tts_model, "voice": voice,
                })
                if "_error" in res:
                    self._send_json({"ok": False, "error": res["_error"]}, status=502)
                    return
                wav_bytes = res["wav"]
                try:
                    with open(cache_path, "wb") as f:
                        f.write(wav_bytes)
                except OSError:
                    pass
                # Backstop GC for the tts cache (same policy as uploads).
                try:
                    _now = __import__("time").time()
                    _alive = []
                    for _f in os.listdir(tts_dir):
                        _p = os.path.join(tts_dir, _f)
                        if not os.path.isfile(_p):
                            continue
                        _mt = os.path.getmtime(_p)
                        if (_now - _mt) > 86400:
                            try: os.remove(_p)
                            except OSError: pass
                        else:
                            _alive.append((_mt, _p))
                    if len(_alive) > 50:
                        _alive.sort(reverse=True)
                        for _mt, _p in _alive[50:]:
                            try: os.remove(_p)
                            except OSError: pass
                except Exception:
                    pass

            # Return raw WAV bytes (frontend plays via Blob URL).
            try:
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(wav_bytes)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(wav_bytes)
            except Exception:
                pass
            return

        # ── /api/upload: 이미지/파일 업로드 (base64 → 파일 저장) ──────────
        if route == "/api/upload":
            import base64, tempfile
            try:
                n = int(self.headers.get("Content-Length") or "0")
                raw = self.rfile.read(n) if n > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8") or "{}")
                data_b64 = payload.get("data", "")
                filename = payload.get("filename", "upload")
                slot = payload.get("slot", "")
                # 저장 디렉토리: ~/.usekit_uploads/
                upload_dir = os.path.join(os.path.expanduser("~"), ".usekit_uploads")
                os.makedirs(upload_dir, exist_ok=True)
                # 고유 파일명 생성 (슬롯명 포함)
                ext = os.path.splitext(filename)[1] or ".bin"
                slot_prefix = "".join(c for c in slot if c.isalnum() or c in "._-") if slot else "noslot"
                safe_name = f"{slot_prefix}_{int(__import__('time').time())}_{filename}"
                # 파일명 sanitize
                safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
                if not safe_name:
                    safe_name = "upload" + ext
                save_path = os.path.join(upload_dir, safe_name)
                # base64 디코딩 → 저장
                file_bytes = base64.b64decode(data_b64)
                with open(save_path, "wb") as f:
                    f.write(file_bytes)
                # ── Backstop GC ──────────────────────────────────────────
                # Users never clean up and images pile up fastest, so defend
                # storage proactively here — independent of slot lifecycle.
                # Two axes: drop anything older than 24h AND keep only the
                # newest N survivors (so a same-day burst can't grow unbounded).
                # The just-saved file is newest, so it always survives.
                try:
                    _GC_TTL = 86400   # 24h
                    _GC_KEEP = 30     # newest N survivors max
                    _now = __import__("time").time()
                    _alive = []
                    for _f in os.listdir(upload_dir):
                        _p = os.path.join(upload_dir, _f)
                        if not os.path.isfile(_p):
                            continue
                        _mt = os.path.getmtime(_p)
                        if (_now - _mt) > _GC_TTL:
                            try: os.remove(_p)
                            except OSError: pass
                        else:
                            _alive.append((_mt, _p))
                    if len(_alive) > _GC_KEEP:
                        _alive.sort(reverse=True)  # newest first
                        for _mt, _p in _alive[_GC_KEEP:]:
                            try: os.remove(_p)
                            except OSError: pass
                except Exception:
                    pass  # GC must never break an upload
                # ─────────────────────────────────────────────────────────
                self._send_json({"ok": True, "path": save_path, "size": len(file_bytes)})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # ── /api/delete-uploads: 슬롯 연동 업로드 파일 일괄 삭제 ──────────
        if route == "/api/delete-uploads":
            import glob as _glob
            try:
                n = int(self.headers.get("Content-Length") or "0")
                raw = self.rfile.read(n) if n > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8") or "{}")
                slot = payload.get("slot", "")
                if not slot:
                    self._send_json({"ok": False, "error": "no slot"}, status=400)
                    return
                upload_dir = os.path.join(os.path.expanduser("~"), ".usekit_uploads")
                slot_prefix = "".join(c for c in slot if c.isalnum() or c in "._-")
                pattern = os.path.join(upload_dir, f"{slot_prefix}_*")
                files = _glob.glob(pattern)
                for f in files:
                    os.remove(f)
                self._send_json({"ok": True, "deleted": len(files)})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        if route != "/api/save":
            self._send_json({"ok": False, "error": "not_found"}, status=404)
            return

        try:
            n = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(n) if n > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:
            self._send_json({"ok": False, "error": f"bad_json:{type(e).__name__}"}, status=400)
            return

        try:
            storage = str(payload.get("storage", "local"))  # "local" or "usekit"
            text = str(payload.get("text", ""))
            
            if storage == "usekit":
                rel_path = str(payload.get("path", ""))
                if not rel_path:
                    self._send_json({"ok": False, "error": "missing_path"}, status=400)
                    return

                # 절대경로면 USEKIT_BASE 기준 상대경로로 정규화
                p = Path(rel_path).expanduser()
                if p.is_absolute():
                    try:
                        rel_path = str(p.resolve().relative_to(USEKIT_BASE))
                    except ValueError:
                        rel_path = str(p.resolve())

                out_path = (USEKIT_BASE / rel_path).resolve()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(text, encoding="utf-8")

                try:
                    rel_display = str(out_path.relative_to(USEKIT_BASE))
                except ValueError:
                    rel_display = str(out_path)

                self._send_json({
                    "ok": True,
                    "storage": "usekit",
                    "path": rel_display,
                    "absolute": str(out_path),
                    "bytes": len(text.encode("utf-8"))
                })
            else:
                # LOCAL 경로: 기존 로직 (dir/name/ext)
                rel_dir = safe_rel_dir(str(payload.get("dir", "")))
                name = safe_token(str(payload.get("name", "")), default="untitled")
                ext = safe_token(str(payload.get("ext", "")), default="txt").lstrip(".")
                
                out_dir = BASE_SAVE_DIR / rel_dir if rel_dir else BASE_SAVE_DIR
                out_dir.mkdir(parents=True, exist_ok=True)
                
                out_path = out_dir / f"{name}.{ext}"
                out_path.write_text(text, encoding="utf-8")
                
                self._send_json({
                    "ok": True,
                    "storage": "local",
                    "path": str(out_path),
                    "bytes": len(text.encode("utf-8"))
                })
        except Exception as e:
            self._send_json({"ok": False, "error": f"save_failed:{type(e).__name__}", "detail": str(e)}, status=500)


def _start_server_thread(root: Path, host: str, port: int):
    handler = lambda *a, **kw: EditorHandler(*a, directory=str(root), **kw)  # noqa: E731
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.allow_reuse_address = True
    th = threading.Thread(target=httpd.serve_forever, name="usekit-editor-http", daemon=True)
    th.start()
    return httpd, th


def _resolve_file_arg(file: str):
    """file 인자를 (resolved_path, initial_data) 로 변환.

    판단 순서:
      1. '/' 포함 or '~' 시작 → path 그대로
      2. '.' 포함(확장자 있음) → '_tmp/{file}' 로 경로 취급
      3. 단순 문자열 → u.fpb(file) 시도
         - hits 있으면 → path
         - 없으면 → (None, file) 신규+바인딩
    """
    if not file:
        return None, None
    if "/" in file or file.startswith("~"):
        return file, None
    if "." in file:
        return f"_tmp/{file}", None
    try:
        import usekit as u  # type: ignore
        hits = u.fpb(file)
        if hits:
            return str(hits[0]), None
    except Exception:
        pass
    return None, file


def main(file: str | None = None, path: str | None = None,
         data: str | None = None, name: str | None = None,
         dir_path: str | None = None,
         initial_data: str | None = None, **kwargs):
    """Launch the editor server.

    Args:
        data:     초기 내용 or 단순이름 (fpb resolve 시도)
        name:     파일명 e.g. "test03" or "test03.py"
        dir_path: 저장 디렉토리 e.g. "/storage/.../src/base/"
        file:     하위호환 단일 경로
        path:     하위호환 저장경로 override
        initial_data: 직접 지정 초기 텍스트
    """
    # Backward compatibility
    if file is None and 'file_path' in kwargs:
        file = kwargs.get('file_path')

    global USEKIT_BASE, ROOT, USEKIT_SANDBOX_ROOT, BASE_SAVE_DIR, USEKIT_SANDBOX_ROOT_REL, _initial_dir_rel

    # Resolve paths (no hard-coded absolute paths)
    USEKIT_BASE = resolve_usekit_base().resolve()
    ROOT = resolve_editor_root().resolve()

    # ── data/name/dir_path → file, initial_data 변환 ──
    if data is not None or name is not None or dir_path is not None:
        # PosixPath → str, 절대경로면 USEKIT_BASE 기준 상대경로로 정규화
        if dir_path is not None:
            dp = Path(str(dir_path)).expanduser().resolve()
            try:
                dir_path = str(dp.relative_to(USEKIT_BASE))  # "src/base"
            except ValueError:
                dir_path = str(dp)  # USEKIT_BASE 밖이면 그대로 (비정상케이스)

        if name is not None:
            fname = name if "." in name else f"{name}.txt"
            if dir_path is not None:
                file = f"{dir_path.rstrip('/')}/{fname}"  # "src/base/test04.txt"
            else:
                try:
                    import usekit as u  # type: ignore
                    hits = u.fpb(name)
                    if hits:
                        dp = Path(str(hits[0])).resolve()
                        try:
                            file = str(dp.relative_to(USEKIT_BASE))
                        except ValueError:
                            file = str(dp)
                    else:
                        file = f"_tmp/{fname}"
                except Exception:
                    file = f"_tmp/{fname}"
        elif dir_path is not None:
            file = dir_path.rstrip("/") + "/"

        if data is not None:
            initial_data = data

    # file 단순이름 resolve (절대경로도 상대경로로 정규화)
    if file is not None and initial_data is None:
        file, initial_data = _resolve_file_arg(file)

    # 혹시 file이 절대경로로 들어왔으면 상대경로로 정규화
    if file is not None and (file.startswith("/") or file.startswith("~")):
        try:
            file = str(Path(file).expanduser().resolve().relative_to(USEKIT_BASE))
        except ValueError:
            pass  # USEKIT_BASE 밖이면 그대로

    # Sandbox root = USEKIT_BASE 루트 (항상 프로젝트 전체 접근 가능)
    # initial_dir: 로드 팝업이 처음 열릴 때 보여줄 폴더 (파일 위치 기준)
    target_file = file or DEFAULT_FILE
    _file_parts = target_file.replace("\\", "/").lstrip("/").split("/")
    _initial_dir_rel = "/".join(_file_parts[:-1]) if len(_file_parts) > 1 else "_tmp"

    USEKIT_SANDBOX_ROOT_REL = ""          # 항상 USEKIT_BASE 루트
    USEKIT_SANDBOX_ROOT = USEKIT_BASE.resolve()

    BASE_SAVE_DIR = (USEKIT_BASE / _initial_dir_rel).resolve()  # save는 파일 위치 기준 유지

    file_exists_or_raise(ROOT)
    file_exists_or_raise(ROOT / PAGE)
    BASE_SAVE_DIR.mkdir(parents=True, exist_ok=True)

    import builtins

    # ✅ If PORT is already listening:
    # - reuse ONLY if it is OUR server (/api/ping ok)
    # - otherwise error (do not fallback to random ports)
    if is_listening(HOST, PORT):
        if is_our_server(HOST, PORT):
            target_file = file or DEFAULT_FILE
            # reuse 시 sandbox root는 항상 USEKIT_BASE 루트
            _file_parts = target_file.replace("\\", "/").lstrip("/").split("/")
            _initial_dir_rel = "/".join(_file_parts[:-1]) if len(_file_parts) > 1 else "_tmp"
            USEKIT_SANDBOX_ROOT_REL = ""
            USEKIT_SANDBOX_ROOT = USEKIT_BASE.resolve()
            BASE_SAVE_DIR = (USEKIT_BASE / _initial_dir_rel).resolve()
            BASE_SAVE_DIR.mkdir(parents=True, exist_ok=True)
            url = build_url(HOST, PORT, PAGE, target_file, initial_data)
            open_browser(url)
            if not QUIET:
                print("ROOT :", ROOT)
                print("FILE :", target_file)
                print("URL  :", url)
                print("PID  : (reused-our-server)")
            return

        raise RuntimeError(
            "PORT 7979 is busy by a different server (no /api/ping).\n"
            "Please free 7979, then retry.\n\n"
            "Termux:\n"
            "  ss -ltnp | grep :7979\n"
            "  pkill -f \"http.server.*7979\"\n"
            "Optional:\n"
            "  pkg install lsof\n"
            "  lsof -i:7979\n"
        )

    # Cleanup stale object in this Python process (optional)
    srv = getattr(builtins, _BUILTIN_KEY, None)
    if srv and isinstance(srv, dict):
        try:
            if srv.get("httpd"):
                srv["httpd"].shutdown()
                srv["httpd"].server_close()
        except Exception:
            pass

    httpd, th = _start_server_thread(ROOT, HOST, PORT)

    if not wait_listen(HOST, PORT, 6.0):
        try:
            httpd.shutdown()
            httpd.server_close()
        except Exception:
            pass
        raise RuntimeError("server failed to start")

    setattr(builtins, _BUILTIN_KEY, {"httpd": httpd, "thread": th, "port": PORT, "root": str(ROOT)})

    target_file = file or DEFAULT_FILE
    url = build_url(HOST, PORT, PAGE, target_file, initial_data)
    open_browser(url)

    if not QUIET:
        print("ROOT :", ROOT)
        print("FILE :", target_file)
        print("URL  :", url)
        print("PID  : (thread-fixed)")

    # nohup/백그라운드 실행 시 메인 스레드 유지 (서버 스레드 보호)
    import sys as _sys, signal as _signal
    if not _sys.stdout.isatty():
        try:
            _signal.pause()  # 시그널 올 때까지 대기 (서버 유지)
        except (AttributeError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    import sys
    # 커맨드라인에서 파일 경로 받기
    # python open_edit.py usekit/tools/editor.js
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_arg)
else:
    # usekit에서 import해서 사용할 때
    main()