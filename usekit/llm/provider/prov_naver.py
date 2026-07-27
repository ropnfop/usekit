# Path: usekit.llm.provider.prov_naver.py
# -----------------------------------------------------------------------
#  Naver Search API client (KOREAN search provider — NOT an LLM provider)
# -----------------------------------------------------------------------
#  Unlike Gemini google_search grounding (where the model searches AND
#  writes inside one call, choosing its own sources), Naver returns raw
#  results to the SERVER. We fetch -> normalize -> inject into the LLM
#  context -> the LLM only summarizes. So source control is 100% server-
#  side here: the model can never cite a result we didn't hand it.
#
#  Auth: HTTP headers X-Naver-Client-Id / X-Naver-Client-Secret
#        (register a free app at https://developers.naver.com — 25,000/day)
#  Endpoint: https://openapi.naver.com/v1/search/{kind}.json
#  This module is intentionally dependency-light and config-agnostic:
#  pass client_id / client_secret in; the chat layer decides where they
#  come from (sys keystore / env / yaml). Nothing here touches the UI.
# -----------------------------------------------------------------------

import re
import html
import requests

_BASE = "https://openapi.naver.com/v1/search/{kind}.json"

# kind -> Naver endpoint segment. Korean-facing surfaces we actually want.
_KINDS = {
    "news": "news",          # 뉴스   — domestic press coverage
    "blog": "blog",          # 블로그 — reviews / how-to / 후기
    "web": "webkr",          # 웹문서 — general Korean web
    "kin": "kin",            # 지식iN — Q&A / 생활정보
    "cafe": "cafearticle",   # 카페글 — community reaction
    "encyc": "encyc",        # 지식백과 — encyclopedic
}

_TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    """Naver wraps matched terms in <b>..</b> and HTML-escapes entities.
    Strip tags and unescape so the text is clean for LLM injection."""
    if not text:
        return ""
    return html.unescape(_TAG_RE.sub("", text)).strip()


def search(
    query: str,
    *,
    client_id: str,
    client_secret: str,
    kind: str = "news",
    count: int = 5,
    sort: str = "sim",       # 'sim' = relevance, 'date' = newest
    timeout: float = 8.0,
) -> dict:
    """Run one Naver search.

    Returns a normalized dict — never raises for API/HTTP errors; the
    caller inspects ``ok``:
        {
          "ok": bool,
          "kind": "news",
          "query": "...",
          "items": [ {title, url, desc, date, source}, ... ],
          "error": str | None,   # set when ok is False
        }
    ``source`` is the result's real domain (news links point at the
    publisher, e.g. yna.co.kr), so the same domain filter used for Gemini
    grounding can be applied here too if desired.
    """
    if not client_id or not client_secret:
        return {"ok": False, "kind": kind, "query": query, "items": [],
                "error": "naver client_id/secret missing"}

    seg = _KINDS.get(kind)
    if not seg:
        return {"ok": False, "kind": kind, "query": query, "items": [],
                "error": f"unknown kind '{kind}'"}

    url = _BASE.format(kind=seg)
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": max(1, min(int(count or 5), 100)),
        "start": 1,
    }
    # 'sort' only applies to news/blog/cafearticle; harmless elsewhere.
    if sort in ("sim", "date"):
        params["sort"] = sort

    try:
        r = requests.get(url, headers=headers, params=params, timeout=timeout)
    except Exception as e:  # network / timeout
        return {"ok": False, "kind": kind, "query": query, "items": [],
                "error": f"request failed: {e}"}

    if r.status_code != 200:
        # 401 = bad keys, 429 = quota, 400 = bad query
        body = (r.text or "")[:200]
        return {"ok": False, "kind": kind, "query": query, "items": [],
                "error": f"http {r.status_code}: {body}"}

    try:
        data = r.json()
    except Exception as e:
        return {"ok": False, "kind": kind, "query": query, "items": [],
                "error": f"bad json: {e}"}

    items = []
    for it in (data.get("items") or []):
        link = it.get("link") or it.get("originallink") or ""
        items.append({
            "title": _clean(it.get("title")),
            "url": link,
            "desc": _clean(it.get("description")),
            "date": it.get("pubDate") or it.get("postdate") or "",
            "source": _domain(link),
        })

    return {"ok": True, "kind": kind, "query": query, "items": items,
            "error": None}


def _domain(url: str) -> str:
    """Bare domain from a real result URL (Naver links point at publishers)."""
    m = re.match(r"https?://([^/]+)/?", url or "")
    if not m:
        return ""
    return m.group(1).lower().lstrip("www.")


def build_context_block(result: dict, *, max_items: int = 5) -> str:
    """Format Naver results for INJECTION into the LLM prompt (the model
    summarizes from these — it must not invent beyond them)."""
    items = (result.get("items") or [])[:max_items]
    if not items:
        return ""
    lines = ["[\uac80\uc0c9 \uacb0\uacfc \u2014 \ub124\uc774\ubc84 (\uc774 \uacb0\uacfc\ub9cc \uadfc\uac70\ub85c \uc0ac\uc6a9, \uc5c6\ub294 \ub0b4\uc6a9 \ucd94\uac00 \uae08\uc9c0)]"]
    for i, it in enumerate(items, 1):
        date = f" ({it['date']})" if it.get("date") else ""
        lines.append(f"[{i}] {it['title']}{date}\n    {it['desc']}\n    {it['url']}")
    return "\n".join(lines)


def build_sources_block(result: dict, *, max_items: int = 5) -> str:
    """Format the visible '— 출처 —' block (mirrors the Gemini path)."""
    items = (result.get("items") or [])[:max_items]
    if not items:
        return ""
    lines = []
    for i, it in enumerate(items, 1):
        src = it.get("source") or ""
        tag = f"{src} \u2014 " if src else ""
        lines.append(f"[{i}] {tag}{it['url']}")
    head = f"\u2014 \ucd9c\ucc98 (\ub124\uc774\ubc84 \uac80\uc0c9 \u00b7 {len(items)}\uac74) \u2014"
    return "\n\n" + head + "\n" + "\n".join(lines)


if __name__ == "__main__":
    # Smoke test — run on-device once you have keys:
    #   NAVER_ID=... NAVER_SECRET=... python -m usekit.llm.provider.prov_naver
    import os
    cid = os.environ.get("NAVER_ID", "")
    sec = os.environ.get("NAVER_SECRET", "")
    res = search("\ud14c\uc2ac\ub77c FSD \uad6d\ub0b4 \ubc18\uc751", client_id=cid,
                 client_secret=sec, kind="news", count=5, sort="date")
    print("ok:", res["ok"], "error:", res["error"])
    print(build_context_block(res))
    print(build_sources_block(res))
