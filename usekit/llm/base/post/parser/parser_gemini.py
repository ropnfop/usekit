# Path: usekit.llm.base.post.parser.parser_gemini.py
# -----------------------------------------------------------------------
#  Parser for Google Gemini responses (SDK + REST)
# -----------------------------------------------------------------------

import json
import re

_FENCE = re.compile(r"```(?:json)?\s*(?P<code>[\s\S]*?)\s*```", re.I)


def _fenced(text):
    if not isinstance(text, str):
        return text
    m = _FENCE.search(text.strip())
    return m.group("code").strip() if m else text.strip()


def _extract_usage(resp):
    """Extract token usage from SDK response or REST dict."""
    usage = {}

    # SDK object
    if hasattr(resp, "usage_metadata"):
        um = resp.usage_metadata
        if um:
            usage = {
                "prompt": getattr(um, "prompt_token_count", None),
                "completion": getattr(um, "candidates_token_count", None),
                "total": getattr(um, "total_token_count", None),
                # implicit/explicit context-cache hit — the part of `prompt`
                # billed at the cached rate (260917 어린왕자: the only way to
                # see whether the prefix cache is actually hitting)
                "cached": getattr(um, "cached_content_token_count", None) or 0,
                "thoughts": getattr(um, "thoughts_token_count", None) or 0,
            }
            return usage

    # REST dict
    if isinstance(resp, dict):
        um = resp.get("usageMetadata") or resp.get("usage_metadata") or {}
        if um:
            usage = {
                "prompt": um.get("promptTokenCount") or um.get("prompt_token_count"),
                "completion": um.get("candidatesTokenCount") or um.get("candidates_token_count"),
                "total": um.get("totalTokenCount") or um.get("total_token_count"),
                "cached": um.get("cachedContentTokenCount") or um.get("cached_content_token_count") or 0,
                "thoughts": um.get("thoughtsTokenCount") or um.get("thoughts_token_count") or 0,
            }
    return usage


_HTTP_IN_ERR = re.compile(r"\b(4\d\d|5\d\d)\b")
_RETRY_IN_ERR = re.compile(r"retry(?:Delay|[ -]?in|[ -]?after)['\":\s]*(\d+(?:\.\d+)?)\s*s?", re.I)


def _status_from_error(raw):
    """(status_code, retry_after) for an error raw. The SDK raises on 429/5xx,
    so the transport code only survives inside the exception text
    ('429 RESOURCE_EXHAUSTED ... retryDelay: 27s'). Read it back out; the
    caller used to guess 429 from elapsed time alone."""
    sc = raw.get("_status_code")
    msg = str(raw.get("_error") or "")
    if sc is None:
        m = _HTTP_IN_ERR.search(msg)
        sc = int(m.group(1)) if m else None
    ra = None
    m = _RETRY_IN_ERR.search(msg)
    if m:
        try:
            ra = float(m.group(1))
        except ValueError:
            ra = None
    return sc, ra


def parse(raw: dict) -> dict:
    """
    Parse Gemini response → unified result dict.

    Handles both SDK response objects and REST JSON.
    """
    if "_error" in raw:
        sc, ra = _status_from_error(raw)
        return {
            "text": "",
            "content": None,
            "usage": {},
            "elapsed": raw.get("_elapsed", 0),
            "provider": "gemini",
            "model": "",
            "status": "error",
            "finish": None,
            "error": raw["_error"],
            "status_code": sc,
            "retry_after": ra,
            "raw": raw,
        }

    mode = raw.get("_mode", "sdk")
    text = ""
    finish = None
    usage = {}

    if mode == "sdk":
        sdk_resp = raw.get("_sdk_response")
        if sdk_resp:
            # SDK .text property
            try:
                text = sdk_resp.text or ""
            except Exception:
                text = str(sdk_resp)

            # finish reason
            try:
                cands = sdk_resp.candidates or []
                if cands:
                    finish = str(cands[0].finish_reason) if cands[0].finish_reason else None
            except Exception:
                pass

            usage = _extract_usage(sdk_resp)

    elif mode == "rest":
        # REST JSON
        candidates = raw.get("candidates") or []
        if candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []
            texts = [p["text"] for p in parts if isinstance(p, dict) and "text" in p]
            text = "\n".join(texts)
            finish = candidates[0].get("finishReason")
        usage = _extract_usage(raw)

    # try json parse
    content = None
    try:
        fenced = _fenced(text)
        if fenced:
            content = json.loads(fenced)
    except (json.JSONDecodeError, TypeError):
        content = None

    return {
        "text": text,
        "content": content,
        "usage": usage,
        "elapsed": raw.get("_elapsed", 0),
        "provider": "gemini",
        "model": "",
        "status": "success" if "_error" not in raw else "error",
        "finish": finish,
        "error": None,
        "status_code": raw.get("_status_code") or 200,
        "retry_after": None,
        "raw": raw,
    }
