# Path: usekit.classes.support.base.init.api.sbi_api.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince × Claude
# — memory is emotion —
#
# API Contract Engine — usekit-provided HTTP server from JSON contract.
#
# Usage:
#   from usekit import us
#
#   us.api.serve("contract/api")                   # serve from @JB alias
#   us.api.serve("contract/api", port=8100)        # custom port
#   us.api.serve(contract_path="/path/to/api.json") # absolute path
#
#   us.api.info("contract/api")                    # print route summary
#   us.api.validate("contract/api")                # validate contract
#   us.api.routes("contract/api")                  # list routes
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import json
import re
from datetime import date
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse, parse_qs


# ===============================================================================
# Response Wrappers
# ===============================================================================

def R(data: Any) -> dict:
    """Standard success response."""
    return {"ok": True, "data": data, "error": None}


def E(msg: str) -> dict:
    """Standard error response."""
    return {"ok": False, "data": None, "error": msg}


# ===============================================================================
# Row Helpers
# ===============================================================================

def _rows(rows) -> list:
    """Convert NamedTuple rows to list of dicts."""
    if not rows:
        return []
    return [dict(zip(r._fields, r)) for r in rows]


def _row(row) -> Optional[dict]:
    """Convert single NamedTuple row to dict."""
    if not row:
        return None
    return dict(zip(row._fields, row))


# ===============================================================================
# Contract Loader
# ===============================================================================

def load_contract(path: str) -> dict:
    """Load contract JSON from file path."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_contract_path(name: str = None, *, contract_path: str = None) -> str:
    """
    Resolve contract file path.

    Args:
        name: KM-style name (e.g., "contract/api" → reads from json/base)
        contract_path: Absolute file path (overrides name)

    Returns:
        Absolute path to contract JSON file.
    """
    if contract_path:
        return contract_path

    if not name:
        raise ValueError("Either name or contract_path required")

    from usekit.classes.common.utils.helper_path import get_smart_path
    route_root = get_smart_path("json", None, None, "base", ensure_ext=False)

    # "contract/api" → contract/api.json
    parts = name.replace(".", "/")
    json_path = route_root / f"{parts}.json"
    if json_path.exists():
        return str(json_path)

    raise FileNotFoundError(f"Contract not found: {json_path}")


# ===============================================================================
# Param Resolution
# ===============================================================================

def _resolve_param(spec: dict, query: dict, body: dict, user_id: str) -> Any:
    """Extract a parameter value from the request context."""
    src = spec.get("from", "body")
    ptype = spec.get("type", "str")
    default = spec.get("default")
    required = spec.get("required", False)
    key = spec.get("key", "")

    if src == "user":
        raw = user_id
    elif src == "query":
        raw = query.get(key, default)
    elif src == "body":
        raw = body.get(key, default)
    else:
        raw = default

    if raw is None and required:
        return None

    if raw is None:
        return default

    if ptype == "int":
        return int(raw)
    elif ptype == "float":
        return float(raw)
    return raw


# ===============================================================================
# Handler Builder
# ===============================================================================

def build_handler(route: dict) -> Optional[Callable]:
    """
    Build a handler function from a contract route spec.

    Returns None for custom handlers.
    Handler signature: (query_params, body, user_id) → dict
    """
    if route.get("handler") == "custom":
        return None

    from usekit import u, ud

    route_id = route["id"]
    target = route.get("target")
    target_sql = route.get("target_sql")
    param_specs = route.get("params", {})
    transform = route.get("transform")
    response_key = route.get("response_key")
    do_commit = route.get("commit", False)
    default_val = route.get("default")
    post_queries = route.get("post_query", [])

    def handler(query_params: dict, body: dict, user_id: str = "user_01"):
        if not ud.is_open():
            ud.conn()

        # Resolve params
        args = {}
        kwargs_extra = {}

        for name, spec in param_specs.items():
            if "key" not in spec:
                real_key = name[:-1] if name.endswith("_") else name
                spec = dict(spec, key=real_key)

            if name == "_kwargs":
                exclude = set(spec.get("exclude", []))
                kwargs_extra = {k: v for k, v in body.items() if k not in exclude}
                continue

            val = _resolve_param(spec, query_params, body, user_id)
            if val is None and spec.get("required"):
                return E(f"{name} required")
            args[name] = val

        try:
            if target:
                fn = u.ipb(target)
                call_args = {n: args[n] for n in param_specs if n != "_kwargs"}
                if kwargs_extra:
                    result = fn(**{**call_args, **kwargs_extra})
                else:
                    result = fn(**call_args)

            elif target_sql:
                bind_keys = route.get("bind") or [k for k in param_specs if k != "_kwargs"]
                bind = tuple(args.get(k, "") for k in bind_keys)
                rows_raw = ud.fetch(target_sql, bind)

                if transform == "one":
                    row = _row(rows_raw[0]) if rows_raw else None
                    result = row if row else default_val
                elif transform == "rows":
                    result = _rows(rows_raw)
                else:
                    result = _rows(rows_raw)
            else:
                return E(f"Route {route_id}: no target or target_sql")

            # Transform module results
            if target and transform == "rows":
                result = _rows(result)
            elif target and transform == "one":
                result = _row(result) if result else default_val

            # Post-queries (enrich rows)
            if post_queries and isinstance(result, list):
                today = date.today().isoformat()
                for pq in post_queries:
                    for row in result:
                        bind_vals = []
                        for b in pq.get("bind", []):
                            if b == "_user_id":
                                bind_vals.append(user_id)
                            elif b == "_today":
                                bind_vals.append(today)
                            else:
                                bind_vals.append(row.get(b, ""))
                        qr = ud.one(pq["sql"], tuple(bind_vals))
                        if qr:
                            for field, ref in pq.get("merge", {}).items():
                                if isinstance(ref, int):
                                    row[field] = qr[ref] if ref < len(qr) else 0
                                elif isinstance(ref, str):
                                    qr_dict = _row(qr) if hasattr(qr, '_fields') else {}
                                    row[field] = qr_dict.get(ref, 0)

            if do_commit:
                ud.conn().commit()

            if response_key:
                return R({response_key: result})
            return R(result)

        except Exception as e:
            return E(str(e))

    handler.__name__ = f"contract_{route_id}"
    return handler


def build_routes(contract: dict, custom_handlers: dict = None) -> tuple:
    """
    Build GET and POST route dicts from contract.

    Returns:
        (routes_get, routes_post)
    """
    custom = custom_handlers or {}
    routes_get = {}
    routes_post = {}

    for route in contract.get("routes", []):
        route_id = route["id"]
        path = route["path"]
        method = route["method"]

        handler = build_handler(route)
        if handler is None:
            handler = custom.get(route_id)
        if handler is None:
            continue

        if method == "GET":
            routes_get[path] = handler
        elif method == "POST":
            routes_post[path] = handler

    return routes_get, routes_post


# ===============================================================================
# HTTP Server
# ===============================================================================

# THREAD-LOCAL (260919): serve() uses ThreadingHTTPServer — every request is
# its own thread — but this used to be a module GLOBAL. Two requests in flight
# could therefore see each other's handler: _default_user() would read the
# OTHER request's X-User-Id, and sse() could write a stream into the other
# request's socket. Both windows were narrow (set at do_* entry, read a few
# lines later) but real once two people share the server (rsrnote.com) and
# once a handler streams for a minute (job SSE). One accessor pair below;
# the do_GET/do_POST bodies read the same as before.
_tls = threading.local()


def _get_handler():
    return getattr(_tls, "handler", None)


def _set_handler(h):
    _tls.handler = h


# ── streaming (SSE) support ─────────────────────────────────────────────────
# us.api.serve normally JSON-wraps every handler return ({ok,data,error}).
# A custom handler that wants to STREAM (Server-Sent Events) instead writes the
# response itself via us.api.sse(...) and returns STREAMED; do_GET/do_POST then
# skip the JSON wrap. Use for token streaming / live progress (e.g. AI chat).
class _Streamed:
    """Sentinel: the handler already wrote the full response; skip JSON wrap."""
    __slots__ = ()


STREAMED = _Streamed()


def sse(events) -> _Streamed:
    """Stream Server-Sent Events from the in-flight request, return STREAMED.

    events: iterable yielding (event_name, data_dict) tuples, OR dicts shaped
            {"event": name, "data": {...}}. Each item is emitted as
            'event: <name>\\ndata: <json>\\n\\n' and flushed immediately.
    Call only from inside a custom handler (uses the active request socket).
    Pattern:
        def my_handler(query, body, user_id="user_01"):
            def gen():
                yield ("meta",  {"phase": "blue"})
                for tok in stream_source(): yield ("delta", {"text": tok})
                yield ("done",  {"turn": 7})
            return us.api.sse(gen())
    """
    h = _get_handler()
    if h is None:                      # not inside a request — nothing to do.
        return STREAMED
    h.send_response(200)
    h.send_header("Content-Type", "text/event-stream; charset=utf-8")
    h.send_header("Cache-Control", "no-cache")
    h._cors()
    # HTTP/1.1 keep-alive never sends EOF without Content-Length → close the
    # socket explicitly so the client's stream reader terminates.
    h.send_header("Connection", "close")
    h.send_header("X-Accel-Buffering", "no")
    h.end_headers()
    h.close_connection = True
    try:
        for ev in events:
            if isinstance(ev, dict):
                name, data = ev.get("event", "message"), ev.get("data", {})
            else:
                name, data = ev
            msg = (f"event: {name}\n"
                   f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n")
            h.wfile.write(msg.encode("utf-8"))
            h.wfile.flush()
    except Exception:
        # client disconnected mid-stream, or the generator raised — stop quietly.
        pass
    return STREAMED


def _default_user(params=None, body=None):
    """Resolve user_id from header > query > body > default."""
    _h = _get_handler()
    if _h is not None:
        hdr = _h.headers.get("X-User-Id", "").strip()
        if hdr:
            return hdr
    if params and params.get("user_id"):
        return params["user_id"]
    if body and body.get("user_id"):
        return body["user_id"]
    return "user_01"


class _APIHandler(BaseHTTPRequestHandler):
    """Generic HTTP handler for contract-based API."""
    routes_get = {}
    routes_post = {}

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-User-Id")

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _params(self):
        return {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        _set_handler(self)
        h = self.routes_get.get(urlparse(self.path).path)
        if not h:
            self._json(E("Not found"), 404)
            return
        try:
            params = self._params()
            uid = _default_user(params)
            result = h(params, {}, uid)
            if result is not STREAMED:        # handler may stream + return STREAMED
                self._json(result)
        except Exception as e:
            self._json(E(str(e)), 500)
        finally:
            _set_handler(None)

    def do_POST(self):
        _set_handler(self)
        h = self.routes_post.get(urlparse(self.path).path)
        if not h:
            self._json(E("Not found"), 404)
            return
        try:
            params = self._params()
            body = self._body()
            uid = _default_user(params, body)
            result = h(params, body, uid)
            if result is not STREAMED:        # handler may stream + return STREAMED
                self._json(result)
        except Exception as e:
            self._json(E(str(e)), 500)
        finally:
            _set_handler(None)

    def log_message(self, fmt, *args):
        pass


# ===============================================================================
# APIHandler — us.api
# ===============================================================================

class APIHandler:
    """
    API contract engine.

    Usage:
        from usekit import us

        # Serve
        us.api.serve("contract/api", port=8100)
        us.api.serve(contract_path="/abs/path/api.json", port=8100,
                     custom={"health": my_health_fn})

        # Inspect
        us.api.info("contract/api")
        us.api.validate("contract/api")
        us.api.routes("contract/api")

        # Stream (SSE) from a custom handler
        return us.api.sse(event_generator)   # then handler returns this
    """

    # Streaming primitives for custom handlers (see module-level sse / STREAMED).
    STREAMED = STREAMED
    sse = staticmethod(sse)

    def serve(
        self,
        name: str = None,
        *,
        contract_path: str = None,
        port: int = 8100,
        host: str = "127.0.0.1",
        custom: dict = None,
    ):
        """
        Start HTTP server from contract JSON.

        Args:
            name: Contract name in json/base (e.g., "contract/api")
            contract_path: Absolute path to contract JSON
            port: Server port (default 8100)
            host: Server host (default 127.0.0.1)
            custom: {"route_id": handler_fn} for custom routes
        """
        from usekit import ud, uw
        import socket

        path = _resolve_contract_path(name, contract_path=contract_path)
        contract = load_contract(path)

        if not ud.is_open():
            ud.conn()

        routes_get, routes_post = build_routes(contract, custom)
        _APIHandler.routes_get = routes_get
        _APIHandler.routes_post = routes_post

        auto_count = len([r for r in contract.get("routes", [])
                          if r.get("handler") != "custom"])
        custom_count = len(custom or {})
        total = len(routes_get) + len(routes_post)

        uw.ok(f"Contract: {Path(path).name} ({auto_count} auto + {custom_count} custom = {total} routes)")

        # ThreadingHTTPServer: handle each request in its own thread so a slow
        # request (e.g. a 30-90s LLM call) doesn't block health/stats/other
        # calls, which otherwise pile up and fail with connect ETIMEDOUT — the
        # exact symptom seen behind a tunnel where requests overlap.
        class _Server(ThreadingHTTPServer):
            allow_reuse_address = True
            daemon_threads = True   # don't hang shutdown on in-flight requests
            def server_bind(self):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                super().server_bind()

        server = _Server((host, port), _APIHandler)
        uw.ok(f"API: http://{host}:{port}")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            ud.close()
            server.server_close()

    def routes(self, name: str = None, *, contract_path: str = None) -> list:
        """List all routes from contract."""
        path = _resolve_contract_path(name, contract_path=contract_path)
        contract = load_contract(path)
        result = []
        for r in contract.get("routes", []):
            result.append({
                "id": r["id"],
                "method": r["method"],
                "path": r["path"],
                "type": "custom" if r.get("handler") == "custom" else "auto",
                "target": r.get("target") or r.get("target_sql", "")[:50],
            })
        return result

    def info(self, name: str = None, *, contract_path: str = None) -> None:
        """Print contract summary."""
        path = _resolve_contract_path(name, contract_path=contract_path)
        contract = load_contract(path)
        routes = contract.get("routes", [])

        auto = [r for r in routes if r.get("handler") != "custom"]
        custom = [r for r in routes if r.get("handler") == "custom"]

        meta = contract.get("_meta", {})
        print(f"[API Contract] {meta.get('project', '?')} v{meta.get('version', '?')}")
        print(f"  Total: {len(routes)} routes ({len(auto)} auto, {len(custom)} custom)")
        print()

        for r in routes:
            rtype = "custom" if r.get("handler") == "custom" else "auto"
            target = r.get("target") or r.get("target_sql", "SQL")[:40] or "—"
            print(f"  [{rtype:6}] {r['method']:4} {r['path']:<25} → {target}")

    def validate(self, name: str = None, *, contract_path: str = None) -> list:
        """
        Validate contract JSON structure.

        Returns list of errors (empty = valid).
        """
        path = _resolve_contract_path(name, contract_path=contract_path)
        contract = load_contract(path)
        errors = []

        if "routes" not in contract:
            errors.append("Missing 'routes' array")
            return errors

        seen_ids = set()
        seen_paths = {}

        for i, r in enumerate(contract["routes"]):
            prefix = f"routes[{i}]"

            if "id" not in r:
                errors.append(f"{prefix}: missing 'id'")
            elif r["id"] in seen_ids:
                errors.append(f"{prefix}: duplicate id '{r['id']}'")
            else:
                seen_ids.add(r["id"])

            if "method" not in r:
                errors.append(f"{prefix}: missing 'method'")
            elif r["method"] not in ("GET", "POST", "PUT", "DELETE"):
                errors.append(f"{prefix}: invalid method '{r['method']}'")

            if "path" not in r:
                errors.append(f"{prefix}: missing 'path'")

            method_path = f"{r.get('method')} {r.get('path')}"
            if method_path in seen_paths:
                errors.append(f"{prefix}: duplicate route '{method_path}'")
            else:
                seen_paths[method_path] = r.get("id")

            # Non-custom must have target or target_sql
            if r.get("handler") != "custom":
                if not r.get("target") and not r.get("target_sql"):
                    errors.append(f"{prefix} ({r.get('id')}): needs 'target' or 'target_sql'")

        return errors

    def __repr__(self):
        return "<APIHandler>"


# Singleton
api = APIHandler()

__all__ = ["APIHandler", "api", "R", "E", "_rows", "_row",
           "load_contract", "build_routes", "build_handler"]
