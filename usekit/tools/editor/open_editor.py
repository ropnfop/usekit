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
        if self.path.startswith("/api/ping"):
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
        
        if self.path.startswith("/api/read_abs"):
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

        if self.path.startswith("/api/read"):
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

        if self.path.startswith("/api/load"):
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
        
        
        if self.path.startswith("/api/list_abs"):
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

        if self.path.startswith("/api/list"):
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

        if self.path.startswith("/api/complete"):
            self._send_json({"ok": True, "items": _get_complete_items()})
            return

        return super().do_GET()


    def do_DELETE(self):
        if self.path.startswith("/api/delete"):
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
        # ── /api/exec: 현재 Python 프로세스에서 코드 실행 ──────────────
        if self.path.startswith("/api/exec"):
            import io, contextlib, threading, traceback
            try:
                length  = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                code    = str(payload.get("code", ""))
                mode    = str(payload.get("mode", "exec"))
                # mode: "exec"       — 기본 exec (RUN 전체, File tmp 래핑)
                #       "single"     — REPL 스타일, 표현식 결과 자동표시 (Line Run)
                #       "block_echo" — exec + 마지막 표현식 echo (Block, Selection, Run Print)
                timeout = min(int(payload.get("timeout", 10)), 30)
                inputs  = list(payload.get("inputs", []))

                # AI 명령은 timeout 상한을 120초로 확장
                _ai_timeout = 120
                _code_preview = str(payload.get("code", "")).lstrip()
                if _code_preview.startswith("!uk ai ") or _code_preview.startswith("!usekit ai "):
                    timeout = min(int(payload.get("timeout", 120)), _ai_timeout)

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
        if self.path.startswith("/api/reset_repl"):
            _init_repl_ns()
            self._send_json({"ok": True, "message": "REPL namespace reset"})
            return

        # ── /api/upload: 이미지/파일 업로드 (base64 → 파일 저장) ──────────
        if self.path.startswith("/api/upload"):
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
                self._send_json({"ok": True, "path": save_path, "size": len(file_bytes)})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # ── /api/delete-uploads: 슬롯 연동 업로드 파일 일괄 삭제 ──────────
        if self.path.startswith("/api/delete-uploads"):
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

        if not self.path.startswith("/api/save"):
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