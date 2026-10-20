# Path: usekit.llm.base.post.parser.parser_openai.py
# -----------------------------------------------------------------------
#  Parser for OpenAI-compatible responses
# -----------------------------------------------------------------------

import json
import re

_FENCE = re.compile(r"```(?:json)?\s*(?P<code>[\s\S]*?)\s*```", re.I)


def _fenced(text):
    """Extract content from markdown code fences."""
    if not isinstance(text, str):
        return text
    m = _FENCE.search(text.strip())
    return m.group("code").strip() if m else text.strip()


def _fmt_retry(seconds):
    """Human-readable retry window from seconds."""
    try:
        s = int(float(seconds))
    except (TypeError, ValueError):
        return ""
    if s <= 0:
        return ""
    if s >= 86400:
        return f"약 {s // 86400}일 후"
    if s >= 3600:
        return f"약 {s // 3600}시간 후"
    if s >= 60:
        return f"약 {s // 60}분 후"
    return f"약 {s}초 후"


def _provider_error_notice(err):
    """Build a user-facing notice from a provider error object.

    Handles the g4f/openai-style rate-limit shape, e.g.
      {"message": "...", "type": "rate_limit_exceeded", "retry_after": 782866,
       "limit": 3, "used": 3}
    Returns (notice_text, is_quota, retry_after) — notice_text empty if not an
    error we should surface.
    """
    if not isinstance(err, dict):
        return ("", False, None)
    etype = (err.get("type") or "").lower()
    msg = err.get("message") or ""
    retry_after = err.get("retry_after")
    is_quota = ("rate_limit" in etype) or ("quota" in etype) or ("limit" in msg.lower())
    if is_quota:
        when = _fmt_retry(retry_after)
        parts = ["⚠ 무료 한도 소진"]
        if err.get("used") is not None and err.get("limit") is not None:
            parts.append(f"(사용 {err.get('used')}/{err.get('limit')})")
        if when:
            parts.append(f"— 회복 {when}")
        notice = " ".join(parts)
        if msg:
            notice += f"\n({msg})"
        return (notice, True, retry_after)
    if msg:
        return (f"⚠ 제공자 오류: {msg}", False, retry_after)
    return ("", False, retry_after)


def parse(raw: dict) -> dict:
    """
    Parse OpenAI-compatible response → unified result dict.

    Input: {"choices": [{"message": {"content": "..."}, ...}], "usage": {...}}
    """
    # error case (network/transport exception captured by adapter)
    if "_error" in raw:
        return {
            "text": "",
            "content": None,
            "usage": {},
            "elapsed": raw.get("_elapsed", 0),
            "provider": "openai",
            "model": "",
            "status": "error",
            "finish": None,
            "error": raw["_error"],
            "raw": raw,
        }

    # Provider error body — even with HTTP 200. Some free proxies (g4f.space)
    # return 200 with {"error": {...rate_limit_exceeded...}} instead of 429,
    # which would otherwise slip through as an empty "(no response)". Detect it,
    # surface a user-facing notice as `text`, and mark quota so the health gate
    # / caller can treat it as a recoverable limit rather than a dead provider.
    _err_obj = raw.get("error")
    if _err_obj:
        notice, is_quota, retry_after = _provider_error_notice(_err_obj)
        if notice:
            return {
                "text": notice,            # shown to user instead of (no response)
                "content": None,
                "usage": {},
                "elapsed": raw.get("_elapsed", 0),
                "provider": "openai",
                "model": raw.get("model", ""),
                "status": "quota" if is_quota else "provider_error",
                "finish": "rate_limit" if is_quota else "error",
                "error": (_err_obj.get("message") if isinstance(_err_obj, dict)
                          else str(_err_obj)),
                "quota": is_quota,
                "retry_after": retry_after,
                "raw": raw,
            }

    # extract text
    choices = raw.get("choices") or [{}]
    choice = choices[0] if choices else {}
    message = choice.get("message") or {}
    text = message.get("content") or ""
    finish = choice.get("finish_reason")

    # Some OpenAI-compatible providers (certain Groq/Llama reasoning models)
    # return an empty `content` and put the actual answer in a reasoning field.
    # Fall back to those so the turn isn't shown as "(no response)".
    if not text:
        text = (message.get("reasoning_content")
                or message.get("reasoning")
                or "")

    # If still empty, surface WHY (P1-3 spirit): finish_reason / status / usage.
    # finish='length' => token cap hit (input too long); empty => provider gave
    # no content. This one-liner makes silent empty responses diagnosable.
    if not text:
        import sys
        print(f"[recv] empty content: provider-raw finish={finish} "
              f"status={raw.get('_status_code')} usage={raw.get('usage')} "
              f"msg_keys={list(message.keys())} err={raw.get('error')}",
              file=sys.stderr)

    # try json parse from fenced block
    content = None
    try:
        fenced = _fenced(text)
        if fenced:
            content = json.loads(fenced)
    except (json.JSONDecodeError, TypeError):
        content = None

    # usage
    usage_raw = raw.get("usage") or {}
    usage = {
        "prompt": usage_raw.get("prompt_tokens"),
        "completion": usage_raw.get("completion_tokens"),
        "total": usage_raw.get("total_tokens"),
        "cached": usage_raw.get("cached_tokens"),   # 261020 implicit-cache hit
    }

    status_code = raw.get("_status_code")
    ok = status_code == 200

    return {
        "text": text,
        "content": content,
        "usage": usage,
        "elapsed": raw.get("_elapsed", 0),
        "provider": "openai",
        "model": raw.get("model", ""),
        "status": "success" if ok else "http_error",
        "finish": finish,
        "error": raw.get("error", {}).get("message") if not ok else None,
        "raw": raw,
    }
