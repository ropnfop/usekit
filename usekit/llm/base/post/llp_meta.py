# Path: usekit.llm.base.post.llp_meta.py
# -----------------------------------------------------------------------
#  Meta extractor — parses {meta, text} from LLM structured response.
#
#  Called after recv parser. If LLM returned structured JSON with meta,
#  extracts and normalizes it. If not, generates minimal meta from text.
# -----------------------------------------------------------------------

import json
import re

_FENCE = re.compile(r"```(?:json)?\s*(?P<code>[\s\S]*?)\s*```", re.I)


def extract_meta(recv_result: dict) -> dict:
    """
    Extract meta from recv result.

    Tries in order:
      1. recv_result["content"] already parsed as dict with "meta" key
      2. Parse from recv_result["text"] (fenced JSON or raw JSON)
      3. Fallback: generate minimal meta from text

    Returns modified recv_result with:
      - "meta": {i, kw, s}  (always present)
      - "text": cleaned text (meta stripped if was embedded)
      - original fields preserved
    """
    result = dict(recv_result)

    # [0] New marker format: "<answer>\n[[META]]{json}". The answer is everything
    # before the marker (already clean + streamable); meta is the trailing JSON.
    raw0 = result.get("text", "")
    if isinstance(raw0, str) and "[[META]]" in raw0:
        idx = raw0.index("[[META]]")
        answer = raw0[:idx].rstrip()
        tail = raw0[idx + len("[[META]]"):].strip()
        meta_obj = {}
        try:
            meta_obj = json.loads(tail)
        except Exception:
            m = re.search(r"\{.*\}", tail, re.S)
            if m:
                try:
                    meta_obj = json.loads(m.group())
                except Exception:
                    meta_obj = {}
        result["meta"] = _normalize_meta(meta_obj)
        result["text"] = answer
        return result

    # [1] Already parsed by recv parser
    content = result.get("content")
    if isinstance(content, dict) and "meta" in content:
        meta = _normalize_meta(content["meta"])
        text = content.get("text", result.get("text", ""))
        # Unescape newlines in text field
        if isinstance(text, str):
            text = text.replace("\\n", "\n")
        result["meta"] = meta
        result["text"] = text
        return result

    # [2] Try parsing from raw text
    raw_text = result.get("text", "")
    parsed = _try_parse_structured(raw_text)
    if parsed:
        meta = _normalize_meta(parsed.get("meta", {}))
        text = parsed.get("text", raw_text)
        if isinstance(text, str):
            text = text.replace("\\n", "\n")
        result["meta"] = meta
        result["text"] = text
        result["content"] = parsed
        return result

    # [3] Fallback: minimal meta from text
    result["meta"] = _fallback_meta(raw_text)
    return result


def _try_parse_structured(text: str) -> dict | None:
    """Try to parse {meta, text} JSON from response text."""
    if not text or not text.strip():
        return None

    # Try fenced block first
    m = _FENCE.search(text)
    candidate = m.group("code").strip() if m else text.strip()

    # Try direct JSON parse
    try:
        obj = json.loads(candidate)
        if isinstance(obj, dict) and "meta" in obj:
            return obj
    except (json.JSONDecodeError, TypeError):
        pass

    # Try finding JSON object in text
    for pattern in [
        re.compile(r'\{[\s\S]*"meta"\s*:\s*\{[\s\S]*\}[\s\S]*"text"\s*:[\s\S]*\}'),
        re.compile(r'\{[\s\S]*"text"\s*:[\s\S]*"meta"\s*:\s*\{[\s\S]*\}[\s\S]*\}'),
    ]:
        match = pattern.search(text)
        if match:
            try:
                obj = json.loads(match.group())
                if isinstance(obj, dict) and "meta" in obj:
                    return obj
            except (json.JSONDecodeError, TypeError):
                continue

    return None


def _normalize_meta(raw_meta: dict) -> dict:
    """Normalize meta fields to consistent types."""
    if not isinstance(raw_meta, dict):
        return {"i": 5, "kw": [], "s": ""}

    i = raw_meta.get("i", 5)
    if not isinstance(i, (int, float)):
        try:
            i = int(i)
        except (ValueError, TypeError):
            i = 5
    i = max(1, min(9, int(i)))

    kw = raw_meta.get("kw", [])
    if isinstance(kw, str):
        kw = [k.strip() for k in kw.split(",") if k.strip()]
    elif not isinstance(kw, list):
        kw = []
    kw = [str(k) for k in kw][:5]  # max 5 keywords

    s = str(raw_meta.get("s", ""))[:80]  # cap summary length

    return {"i": i, "kw": kw, "s": s}


def _fallback_meta(text: str) -> dict:
    """Generate minimal meta when LLM didn't follow format."""
    s = text[:50].replace("\n", " ").strip() if text else ""
    if len(text) > 50:
        s = s[:47] + "..."
    return {
        "i": 5,
        "kw": [],
        "s": s,
    }


__all__ = ["extract_meta"]
