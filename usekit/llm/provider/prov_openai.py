# Path: usekit.llm.provider.prov_openai.py
# -----------------------------------------------------------------------
#  OpenAI-compatible provider (Qwen, vLLM, Ollama, OpenAI, etc.)
# -----------------------------------------------------------------------

import os
import time
import json
import requests
from usekit.llm.provider import ProviderBase


# --------------------------------------------------------------------------
#  Server-side grounding source filter
# --------------------------------------------------------------------------
#  Gemini google_search grounding returns real source URLs, but the model
#  picks WHICH ones to cite on its own and ignores prompt-level "don't use X"
#  rules. So we enforce source quality on the SERVER, not in the prompt.
#
#  NOTE: the grounding uri is a vertexaisearch redirect that does NOT contain
#  the real domain — the domain lives in web.title (e.g. "teslascope.com").
#  So we match against the TITLE, not the uri.
#
#  Defaults below are tuned for the Tesla/FSD test case; this is a generic
#  quality list (block content farms / fan blogs / trackers, trust primary
#  sources + major wires). Edit freely or later move to sys_ai.yaml.
TRUSTED_DOMAINS = (
    # primary / regulator / standards
    "tesla.com", "nhtsa.gov", "sae.org", "unece.org", "europa.eu", "rdw.nl",
    ".gov", ".go.kr", "ec.europa.eu",
    # major wires / press
    "reuters.com", "apnews.com", "bloomberg.com", "wsj.com", "ft.com",
    "nytimes.com", "theguardian.com", "bbc.co", "cnbc.com", "axios.com",
    "electrek.co",
)

BLOCKED_DOMAINS = (
    "youtube.com", "teslarati.com", "teslaoracle.com", "teslascope.com",
    "tessie.com", "wikipedia.org", "basenor.com", "zacks.com",
    "teslaacessories.com", "tesmag", "notanfsdtracker.com", "acvauctions.com",
    "teslahubs.com", "evwire.com", "cleantechnica.com", "reddit.com",
    "medium.com", "fifthlevelconsulting.com", "driveclick.cy", "panterlaw.com",
)


def _domain_of(title: str, uri: str) -> str:
    """The grounding redirect uri hides the real domain; web.title carries it.
    Fall back to uri only if title is empty."""
    return ((title or "") or (uri or "")).lower()


def _classify_source(title: str, uri: str) -> str:
    """Return 'blocked' | 'trusted' | 'other' for a grounding source."""
    dom = _domain_of(title, uri)
    if any(b in dom for b in BLOCKED_DOMAINS):
        return "blocked"
    if any(t in dom for t in TRUSTED_DOMAINS):
        return "trusted"
    return "other"


# --- GEMINI KEY POOL (260709 어린왕자) --------------------------------------------
# Free-tier users ride the OPERATOR's key pool (freemium taste); BYOK users pin
# their own key (config["byok"]=True + api_key -> pool bypassed, no rotation).
# Sources: env GEMINI_API_KEYS ("k1,k2,..") > ~/.usekit/gemini_keys.txt (one key
# per line, # comments ok, kept OUT of git) > empty (single-key behavior exactly
# as before — zero-config no-op). A key that answers 429/403 is BENCHED: burst
# (rate) 90s, daily (RESOURCE_EXHAUSTED "PerDay") until the next 08:00 UTC
# (≈ Pacific midnight, when Google resets daily quota; ≤1h coarse under DST).
# Benching is per-KEY (a per-model 429 over-benches that key for other models —
# accepted v0 coarseness; the model chain upstream covers the gap).
import time as _ktime

_KEY_FILE = os.path.join(os.path.expanduser("~"), ".usekit", "gemini_keys.txt")
_key_cache = {"mtime": None, "keys": []}
_key_rest_until = {}     # key -> epoch ts while benched
_key_cursor = {"i": 0}   # round-robin start (sticky on last good key)


def _pool_keys():
    """Ordered operator key list. env wins; file reloads on mtime change."""
    env = os.environ.get("GEMINI_API_KEYS", "").strip()
    if env:
        return [k.strip() for k in env.split(",") if k.strip()]
    try:
        mt = os.path.getmtime(_KEY_FILE)
    except OSError:
        return []
    if _key_cache["mtime"] != mt:
        try:
            with open(_KEY_FILE, encoding="utf-8") as f:
                _key_cache["keys"] = [ln.strip() for ln in f
                                      if ln.strip() and not ln.strip().startswith("#")]
            _key_cache["mtime"] = mt
        except OSError:
            return []
    return list(_key_cache["keys"])


def _pool_bench(key, daily=False):
    if daily:
        # next 08:00 UTC = Pacific midnight (quota reset), coarse under DST
        now = _ktime.time()
        day = 86400
        nxt = (int(now // day)) * day + 8 * 3600
        if nxt <= now:
            nxt += day
        _key_rest_until[key] = nxt
    else:
        _key_rest_until[key] = _ktime.time() + 90


def _pool_order(pool):
    """Live keys first (round-robin from the last good cursor), benched last."""
    n = len(pool)
    rot = [pool[(_key_cursor["i"] + j) % n] for j in range(n)]
    now = _ktime.time()
    live = [k for k in rot if _key_rest_until.get(k, 0) <= now]
    rest = [k for k in rot if _key_rest_until.get(k, 0) > now]
    return live + rest


def _resolve_model_id(model: str) -> str:
    """Safety-net alias resolver applied at the HTTP boundary.

    Resolves a UI alias (e.g. 'g25f' / 'G25F') to its full model id
    ('gemini-2.5-flash'). resolve_model is case-insensitive and idempotent:
    a full id or an unknown value passes through unchanged. This guards any
    entry path that skipped serve_chat's resolve step — e.g. continue/session
    calls that reuse a stored, un-resolved alias — so the model string sent to
    the API is always a real model name, never a raw alias like 'g25f'.
    """
    if not model:
        return model
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_meta import resolve_model
        return resolve_model(model) or model
    except Exception:
        return model


class ProvOpenAI(ProviderBase):
    """OpenAI-compatible REST API adapter."""

    name = "openai"

    def connect(self, config: dict) -> dict:
        """Validate endpoint reachability."""
        base_url = config.get("base_url", "")
        api_key = config.get("api_key", "")
        model = config.get("model", "")

        if not base_url:
            raise ValueError("[prov_openai] base_url required")

        return {
            "provider": self.name,
            "base_url": base_url.rstrip("/"),
            "api_key": api_key,
            "model": model,
        }

    def send(self, prompt: str, config: dict) -> dict:
        """POST /chat/completions → raw response dict.

        Raw single-prompt path (ua.run / ua.send — no chat pipeline, no system/
        history/meta injection). For the Gemini endpoint this routes to the
        native path (which has no /chat/completions): streams when config
        ['on_delta'] is callable, else a single blocking call. Wrapping the
        prompt as one user message mirrors send_messages so recv parses it the
        same. Non-Gemini providers keep the OpenAI-compatible path below.
        """
        base_url = config["base_url"]
        api_key = config.get("api_key", "")
        model = _resolve_model_id(config.get("model", ""))

        on_delta = config.get("on_delta")
        if "generativelanguage.googleapis.com" in base_url:
            out = self._gemini_native(
                [{"role": "user", "content": prompt}], config,
                on_delta=on_delta if callable(on_delta) else None)
            if out is not None:
                return out
            # native failed → last-resort OpenAI-compat blocking below.

        # generation params
        temperature = config.get("temperature", 0.3)
        max_tokens = config.get("max_tokens", 1200)

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        # Forward provider-specific reasoning controls when present in config
        # (e.g. groq gpt-oss). reasoning_format="hidden" keeps chain-of-thought
        # OUT of `content` so a reasoning model can't bleed CoT / a runaway self-
        # verification loop into the answer; reasoning_effort caps thinking depth.
        # Conditional → no-op for providers/configs that don't set them. The
        # response-parsing (recv) path is untouched.
        for _rk in ("reasoning_effort", "reasoning_format"):
            _rv = config.get(_rk)
            if _rv:
                body[_rk] = _rv

        started = time.time()
        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=body,
                timeout=(10, 180),
            )
            elapsed = round(time.time() - started, 3)
            data = resp.json()
            data["_elapsed"] = elapsed
            data["_status_code"] = resp.status_code
            return data

        except Exception as e:
            elapsed = round(time.time() - started, 3)
            return {
                "_elapsed": elapsed,
                "_status_code": None,
                "_error": str(e),
            }

    def _gemini_native(self, messages: list, config: dict, on_delta=None):
        """Native Gemini call via the generativelanguage endpoint.

        The OpenAI-compat /chat/completions layer streams unreliably AND, on the
        2.5 thinking models, can burn the whole token budget on hidden reasoning
        and return EMPTY visible text. So for Gemini we hit the native endpoint
        directly with thinking DISABLED (thinkingBudget=0), which guarantees a
        visible answer and reliable SSE.

        on_delta callable → stream (streamGenerateContent?alt=sse, real-time tokens).
        on_delta None     → single blocking call (generateContent).
        Converts OpenAI messages → Gemini contents + systemInstruction, returns an
        OpenAI-shaped dict so the parser is unchanged, or None on failure (caller
        then falls back to the OpenAI-compat path).
        """
        base_url = config["base_url"]
        api_key = config.get("api_key", "")
        model = _resolve_model_id(config.get("model", ""))
        streaming = callable(on_delta)

        # base_url is ".../v1beta/openai" → native root is ".../v1beta".
        root = base_url[:-len("/openai")] if base_url.endswith("/openai") else base_url
        verb = "streamGenerateContent?alt=sse" if streaming else "generateContent"
        url = f"{root}/models/{model}:{verb}"
        # KEY POOL: BYOK pins the caller's key; otherwise the operator pool
        # (if configured) rotates on quota faults. Empty pool = single key as before.
        _pool = [] if config.get("byok") else _pool_keys()
        _keys = _pool_order(_pool) if _pool else [api_key]

        def _hdr(k):
            return {"Content-Type": "application/json", "x-goog-api-key": k}

        def _quota_fault(status, body):
            if status == 429:
                return True
            return status == 403 and ("quota" in body.lower()
                                      or "RESOURCE_EXHAUSTED" in body)

        def _bench_and_log(k, status, body):
            daily = "PerDay" in body or "per day" in body.lower()
            _pool_bench(k, daily=daily)
            try:
                import sys as _sys
                _tag = f"…{k[-6:]}" if k else "?"
                print(f"[gemini_keys] {_tag} benched"
                      f"({'daily' if daily else 'burst'}) on {status} model={model}",
                      file=_sys.stderr)
            except Exception:
                pass
        headers = _hdr(_keys[0])

        # OpenAI messages → Gemini contents (+ systemInstruction).
        contents = []
        sys_parts = []
        for m in messages:
            role = m.get("role")
            c = m.get("content")
            if isinstance(c, list):  # vision-style parts: keep text only here
                txt = "".join(p.get("text", "") for p in c
                              if isinstance(p, dict) and p.get("type") == "text")
            else:
                txt = c or ""
            if role == "system":
                if txt:
                    sys_parts.append(txt)
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": txt}]})
            else:
                contents.append({"role": "user", "parts": [{"text": txt}]})

        # Vision: attach config['images'] (data: URLs) as inlineData on the most
        # recent user turn so the model actually SEES them. Gemini REST v1beta
        # uses inlineData{mimeType,data}. Non-data/garbage entries are skipped.
        _imgs = config.get("images") or []
        if _imgs:
            last_user = next((c for c in reversed(contents)
                              if c.get("role") == "user"), None)
            if last_user is None:
                last_user = {"role": "user", "parts": []}
                contents.append(last_user)
            for img in _imgs:
                s = img if isinstance(img, str) else ""
                if s.startswith("data:") and ";base64," in s:
                    head, b64 = s.split(";base64,", 1)
                    mime = head[len("data:"):] or "image/jpeg"
                    last_user["parts"].append(
                        {"inlineData": {"mimeType": mime, "data": b64}})

        # Output budget: search turns thinking ON, and a thinking model can eat the
        # whole budget → the visible answer truncates mid-sentence. Floor the cap
        # so both fit (8K for search, 4K otherwise). Respect higher user settings.
        _max_out = config.get("max_tokens", 1200) or 1200
        _max_out = max(_max_out, 8192 if config.get("search") else 4096)
        gen_cfg = {
            "temperature": config.get("temperature", 0.3),
            "maxOutputTokens": _max_out,
        }
        # Thinking OFF by default: flash-lite/flash otherwise spend the whole
        # budget on hidden reasoning and return EMPTY visible text. EXCEPTION:
        # search grounding needs the model to DECIDE to call google_search, which
        # it won't do with zero thinking → it just answers "I can't access
        # realtime info". So leave thinking at its default when 검색 is active.
        # Thinking budget. OFF (0) normally so flash-lite emits the answer instead
        # of burning the budget on hidden reasoning. For search we need thinking ON
        # (to decide to call google_search) — BUT a heavy thinking model (e.g. G3F)
        # expands thinking to consume the ENTIRE output budget, truncating the
        # visible answer (raising maxOutputTokens just gives thinking more room).
        # So CAP it: enough to trigger search, bounded so the answer always fits.
        # Per-task thinking. Default OFF (flash/flash-lite otherwise burn the whole
        # budget on hidden reasoning and return EMPTY visible text). Search needs
        # thinking ON to decide to call google_search. Otherwise honor a per-task
        # config["thinking"] = {"level": "minimal|low|medium|high", "budget": int}
        # produced upstream (fop.select_thinking): gemini-3 reads thinkingLevel,
        # gemini-2.5 reads thinkingBudget. No config["thinking"] -> off (minimal/0).
        if config.get("search"):
            gen_cfg["thinkingConfig"] = {"thinkingBudget": 2048}
        else:
            _think = config.get("thinking") or {}
            if str(model).startswith("gemini-3"):
                gen_cfg["thinkingConfig"] = {"thinkingLevel": _think.get("level") or "minimal"}
            else:
                gen_cfg["thinkingConfig"] = {"thinkingBudget": int(_think.get("budget") or 0)}
        payload = {"contents": contents, "generationConfig": gen_cfg}
        if sys_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(sys_parts)}]}
        # Search grounding: when 검색 is ON, attach the Google Search tool so the
        # model actually grounds on live results (native path dropped this before,
        # so it answered from training → generic "how to search" replies).
        if config.get("search"):
            payload["tools"] = [{"google_search": {}}]

        def _shape(text, finish, usage, elapsed):
            return {
                "choices": [{
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": (finish or "stop").lower(),
                }],
                "usage": usage,
                "_elapsed": elapsed,
                "_status_code": 200,
                "_streamed": streaming,
            }

        def _usage(um):
            um = um or {}
            return {
                "prompt_tokens": um.get("promptTokenCount"),
                "completion_tokens": um.get("candidatesTokenCount"),
                "total_tokens": um.get("totalTokenCount"),
            }

        def _fmt_sources(chunks):
            # Build a sources block from the REAL search results Gemini returns in
            # groundingMetadata.groundingChunks[].web.{uri,title}. These come from
            # the search engine — not the model's prose — so they never hallucinate
            # and don't drift between runs (the whole point of this).
            #
            # SERVER-SIDE QUALITY FILTER: the model can't be trusted to pick good
            # sources (it cites blocked trackers/blogs regardless of prompt rules),
            # so we classify every source here. Blocked domains are dropped (with a
            # count for transparency); trusted ones are marked ✓ and listed first;
            # the rest are kept as "기타" so the block is never empty on a near-miss.
            seen = set()
            trusted, other, blocked_n = [], [], 0
            for ch in (chunks or []):
                web = (ch or {}).get("web") or {}
                uri = web.get("uri") or ""
                title = web.get("title") or uri
                if not uri or uri in seen:
                    continue
                seen.add(uri)
                kind = _classify_source(title, uri)
                if kind == "blocked":
                    blocked_n += 1
                elif kind == "trusted":
                    trusted.append((title, uri))
                else:
                    other.append((title, uri))

            if not trusted and not other:
                return ""

            lines, n = [], 0
            for title, uri in trusted:
                n += 1
                lines.append(f"[{n}] \u2713 {title} \u2014 {uri}")
            for title, uri in other:
                n += 1
                lines.append(f"[{n}] {title} \u2014 {uri}")

            head = f"\u2014 \ucd9c\ucc98 (\uc2e4\uc2dc\uac04 \uac80\uc0c9 \u00b7 \uc2e0\ub8b0 {len(trusted)} \u00b7 \uae30\ud0c0 {len(other)}"
            if blocked_n:
                head += f" \u00b7 \ube44\uc2e0\ub8b0 {blocked_n}\uac1c \uc81c\uc678"
            head += ") \u2014"
            return "\n\n" + head + "\n" + "\n".join(lines)

        started = time.time()
        try:
            if streaming:
                resp = None
                for _ki, _k in enumerate(_keys):
                    resp = requests.post(url, headers=_hdr(_k), json=payload,
                                         timeout=(10, 180), stream=True)
                    if _quota_fault(resp.status_code, ""):
                        # stream body not read yet; 429 status alone is enough
                        _bench_and_log(_k, resp.status_code, "")
                        try:
                            resp.close()
                        except Exception:
                            pass
                        continue
                    break
                if resp.status_code != 200:
                    try:
                        import sys as _sys
                        _body = resp.text[:300]
                        print(f"[gemini_native] stream {resp.status_code}: {_body}", file=_sys.stderr)
                    except Exception:
                        pass
                    try:
                        resp.close()
                    except Exception:
                        pass
                    return None
                resp.encoding = "utf-8"   # SSE is UTF-8; requests else guesses latin-1 → 한글 깨짐
                MARKER = "[[META]]"
                full = ""        # everything the model emits (answer + [[META]]{...})
                emitted = 0      # how much of the ANSWER we've already streamed out
                finish, usage = None, {}
                grounding_chunks = []   # real search sources (groundingMetadata)

                def _emit(final=False):
                    # Stream only the answer portion (before [[META]]). Hold back the
                    # last few chars until we're sure they aren't a forming marker.
                    nonlocal emitted
                    mi = full.find(MARKER)
                    if mi != -1:
                        if mi > emitted:
                            try:
                                on_delta(full[emitted:mi])
                            except Exception:
                                pass
                        emitted = len(full)   # freeze: nothing after the marker streams
                        return
                    end = len(full) if final else len(full) - (len(MARKER) - 1)
                    if end > emitted:
                        try:
                            on_delta(full[emitted:end])
                        except Exception:
                            pass
                        emitted = end

                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if line.startswith("data:"):
                        line = line[5:].strip()
                    if not line or line == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(line)
                    except Exception:
                        continue
                    cand = (chunk.get("candidates") or [{}])[0]
                    for p in ((cand.get("content") or {}).get("parts")) or []:
                        piece = p.get("text") or ""
                        if piece:
                            full += piece
                            _emit()
                    if cand.get("finishReason"):
                        finish = cand["finishReason"]
                    if chunk.get("usageMetadata"):
                        usage = _usage(chunk["usageMetadata"])
                    # Grounding sources arrive (usually in the final chunk). Keep the
                    # richest set seen so far.
                    _gm = (cand.get("groundingMetadata") or {}).get("groundingChunks")
                    if _gm and len(_gm) > len(grounding_chunks):
                        grounding_chunks = _gm
                _emit(final=True)   # flush any held-back tail (when no marker present)
                if not full.strip():
                    # EMPTY DIAGNOSIS (260709): same as the non-streaming path.
                    try:
                        import sys as _sys
                        print(f"[gemini_native] empty(stream): model={model} "
                              f"finish={finish} usage={usage}", file=_sys.stderr)
                    except Exception:
                        pass
                    return None
                # Append the REAL search sources (stream them in + keep in content).
                _src = _fmt_sources(grounding_chunks)
                if not _src and config.get("search"):
                    # Search was ON but the model returned no grounding → it didn't
                    # actually search. Say so loudly so the user never mistakes the
                    # model's self-written URLs for real ones.
                    _src = ("\n\n⚠️ 실시간 검색 결과 없음 — 이 모델이 google_search를 "
                            "수행하지 않았습니다. 본문의 출처·URL은 지어낸 것일 수 있으니 "
                            "신뢰하지 마세요. (검색되는 모델, 예: G25F로 바꿔보세요.)")
                if _src:
                    try:
                        on_delta(_src)
                    except Exception:
                        pass
                    full += _src
                # Return the FULL raw (answer + [[META]]{...}); extract_meta splits it.
                return _shape(full, finish, usage, round(time.time() - started, 3))

            # non-streaming — walk the key pool on quota faults (429/403-quota),
            # any other fault falls through to the existing non-200 handling.
            resp = None
            for _ki, _k in enumerate(_keys):
                resp = requests.post(url, headers=_hdr(_k), json=payload,
                                     timeout=(10, 180))
                if _quota_fault(resp.status_code, resp.text or ""):
                    _bench_and_log(_k, resp.status_code, resp.text or "")
                    continue
                if _pool and _pool_keys():
                    try:
                        _key_cursor["i"] = _pool_keys().index(_k)   # sticky good key
                    except ValueError:
                        pass
                break
            if resp.status_code != 200:
                # EMPTY DIAGNOSIS v2 (260709): a non-200 here was SILENT — a 429
                # quota hit / 400 / 503 fell through to the compat path and
                # surfaced upstream as a bare "empty response", indistinguishable
                # from a content block. Log status + body head (the 429 body
                # carries RESOURCE_EXHAUSTED / retry info verbatim).
                try:
                    import sys as _sys
                    print(f"[gemini_native] http {resp.status_code} model={model}: "
                          f"{resp.text[:300]}", file=_sys.stderr)
                except Exception:
                    pass
                return None
            resp.encoding = "utf-8"
            data = resp.json()
            cand = (data.get("candidates") or [{}])[0]
            parts = ((cand.get("content") or {}).get("parts")) or []
            text = "".join(p.get("text", "") for p in parts if p.get("text"))
            if not text.strip():
                # EMPTY DIAGNOSIS (260709): Gemini always says WHY it returned
                # nothing — promptFeedback.blockReason (input blocked before
                # generation, fast) / finishReason SAFETY|RECITATION (output
                # suppressed) / MAX_TOKENS with thoughtsTokenCount (thinking
                # starved the budget, slow). Dropping these made every empty
                # look identical upstream ("empty response"), so the fix
                # (fallback model vs thinking control) could not be chosen.
                # Log to stderr (lands in the api log); behavior unchanged.
                try:
                    import sys as _sys
                    _fb = (data.get("promptFeedback") or {}).get("blockReason")
                    _fr = cand.get("finishReason")
                    _um = data.get("usageMetadata") or {}
                    _sr = [f"{(r or {}).get('category','?')}="
                           f"{(r or {}).get('probability','?')}"
                           for r in (cand.get("safetyRatings") or []) if r]
                    print(f"[gemini_native] empty: model={model} finish={_fr} "
                          f"block={_fb} thoughts={_um.get('thoughtsTokenCount')} "
                          f"total={_um.get('totalTokenCount')} safety={_sr}",
                          file=_sys.stderr)
                except Exception:
                    pass
                return None
            _src = _fmt_sources((cand.get("groundingMetadata") or {}).get("groundingChunks"))
            if not _src and config.get("search"):
                _src = ("\n\n⚠️ 실시간 검색 결과 없음 — 이 모델이 google_search를 수행하지 "
                        "않았습니다. 본문의 출처·URL은 신뢰하지 마세요.")
            if _src:
                text += _src
            return _shape(text, cand.get("finishReason"),
                          _usage(data.get("usageMetadata")),
                          round(time.time() - started, 3))
        except Exception:
            return None

    def send_messages(self, messages: list, config: dict) -> dict:
        """POST /chat/completions with full messages array.

        When config['on_delta'] is callable AND this is the Gemini endpoint, stream
        natively (real-time tokens). Otherwise (or on streaming failure) fall back
        to a single blocking request — zero behavior change for non-streaming.
        """
        base_url = config["base_url"]
        api_key = config.get("api_key", "")
        model = _resolve_model_id(config.get("model", ""))

        temperature = config.get("temperature", 0.3)
        max_tokens = config.get("max_tokens", 1200)

        on_delta = config.get("on_delta")
        is_gemini = "generativelanguage.googleapis.com" in base_url
        if is_gemini:
            # Native path (thinking disabled): streams if on_delta, else blocks.
            out = self._gemini_native(messages, config,
                                      on_delta=on_delta if callable(on_delta) else None)
            if out is not None:
                return out
            # native failed → last-resort OpenAI-compat blocking below.

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        # Forward provider-specific reasoning controls when present in config
        # (e.g. groq gpt-oss). reasoning_format="hidden" keeps chain-of-thought
        # OUT of `content` so a reasoning model can't bleed CoT / a runaway self-
        # verification loop into the answer; reasoning_effort caps thinking depth.
        # Conditional → no-op for providers/configs that don't set them. The
        # response-parsing (recv) path is untouched.
        for _rk in ("reasoning_effort", "reasoning_format"):
            _rv = config.get(_rk)
            if _rv:
                body[_rk] = _rv

        started = time.time()
        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=body,
                timeout=(10, 180),
            )
            elapsed = round(time.time() - started, 3)
            data = resp.json()
            data["_elapsed"] = elapsed
            data["_status_code"] = resp.status_code
            return data

        except Exception as e:
            elapsed = round(time.time() - started, 3)
            return {
                "_elapsed": elapsed,
                "_status_code": None,
                "_error": str(e),
            }

    def ping(self, config: dict) -> dict:
        """Lightweight ping via minimal generate."""
        ping_cfg = {**config, "max_tokens": 5, "temperature": 0}
        result = self.send("Hi", ping_cfg)
        ok = result.get("_status_code") == 200 and "_error" not in result
        return {"ok": ok, "elapsed": result.get("_elapsed", 0)}

    def close(self) -> None:
        pass  # stateless REST
