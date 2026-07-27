# Path: usekit.llm.parallel.llp_recall.py
# -----------------------------------------------------------------------
#  Recall engine — usekit 내부 자원 검색 + 병렬 수집 + 병합
#
#  ua.chat("u.wjb append 예제", recall=True)
#  ua.chat("SQL 저장 방법", recall=True, verify=True)
#
#  Flow:
#    1. intent → 필요한 source 판별 (로컬, 0ms)
#    2. local workers → usekit help/docs/examples/source 병렬 검색
#    3. merge → LLM이 수집 결과를 종합
#    4. verify (optional) → 예제 코드 실행 + 결과 첨부
#    5. gap check → 빈 곳 있으면 2차 수집
#
#  Local workers는 LLM을 호출하지 않음.
#  merge 단계에서만 LLM 1회 호출.
# -----------------------------------------------------------------------

import os
import re
import time
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════
#  dispatch_recall — main entry (called by ua._chat_recall)
# ══════════════════════════════════════════════════════════════════════

def dispatch_recall(handler, prompt, context="", verify=False, **kw):
    """
    Recall + merge + optional verify.

    Args:
        handler:  AIHandler instance
        prompt:   user prompt
        context:  compressed history string
        verify:   run code examples if True
        **kw:     extra options

    Returns:
        {text, mode, sources, verified, elapsed}
    """
    t0 = time.time()

    # [1] Intent → which sources to search
    sources_needed = _detect_sources(prompt)
    if not sources_needed:
        # Nothing to recall — pass through
        return {
            "text": "",
            "mode": "recall_skip",
            "sources": [],
            "verified": False,
            "elapsed": 0,
        }

    # [2] Parallel local search
    gathered = _gather(prompt, sources_needed)

    # [3] Gap check + 2nd round
    gaps = _find_gaps(prompt, gathered)
    if gaps:
        more = _gather(prompt, gaps)
        gathered.extend(more)

    # [4] Merge via LLM (single call)
    merged = _merge(handler, prompt, gathered, context)

    # [5] Verify (optional)
    verified_results = []
    if verify:
        verified_results = _verify(merged)

    elapsed = round(time.time() - t0, 3)

    # Build final text
    text = merged
    if verified_results:
        text += "\n\n── 실행 검증 ──\n"
        for vr in verified_results:
            text += f"\n>>> {vr['code']}\n{vr['result']}\n"

    return {
        "text": text,
        "mode": "recall",
        "sources": [g["source"] for g in gathered if g.get("found")],
        "verified": bool(verified_results),
        "elapsed": elapsed,
    }


# ── Intent detection ─────────────────────────────────────────────

# usekit API 패턴: u.wjb, u.rjb, ua.chat, ud.fetch, etc.
_USEKIT_API = re.compile(r'\bu[adwts]?\.\w+', re.I)

# Source types
HELP = "help"
DOCS = "docs"
EXAMPLES = "examples"
SOURCE = "source"


def _detect_sources(prompt):
    """
    Determine which internal sources are relevant.

    Returns list of source types to search.
    """
    p = prompt.lower()
    sources = []

    # usekit API mention → help + source + examples
    if _USEKIT_API.search(prompt):
        sources.extend([HELP, SOURCE, EXAMPLES])

    # Explicit signals
    if any(s in p for s in ["예제", "example", "샘플", "sample", "코드"]):
        if EXAMPLES not in sources:
            sources.append(EXAMPLES)

    if any(s in p for s in ["문서", "docs", "설명", "도움말", "help", "사용법", "방법"]):
        if HELP not in sources:
            sources.append(HELP)
        if DOCS not in sources:
            sources.append(DOCS)

    if any(s in p for s in ["소스", "source", "구현", "implementation", "내부", "코드"]):
        if SOURCE not in sources:
            sources.append(SOURCE)

    if any(s in p for s in ["sql", "db", "테이블", "쿼리", "query"]):
        if HELP not in sources:
            sources.append(HELP)
        if EXAMPLES not in sources:
            sources.append(EXAMPLES)

    return sources


# ── Gather (local workers, no LLM) ──────────────────────────────

def _gather(prompt, sources):
    """
    Run local search workers in parallel.

    Each worker searches a different usekit resource.
    No LLM calls — pure file/API lookups.
    """
    results = []

    with ThreadPoolExecutor(max_workers=min(4, len(sources))) as pool:
        futures = {}
        for src in sources:
            worker = _WORKERS.get(src)
            if worker:
                f = pool.submit(worker, prompt)
                futures[f] = src

        for f in as_completed(futures):
            src = futures[f]
            try:
                data = f.result(timeout=5)
                results.append({
                    "source": src,
                    "found": bool(data),
                    "data": data or "",
                })
            except Exception as e:
                results.append({
                    "source": src,
                    "found": False,
                    "data": f"(error: {e})",
                })

    return results


# ── Local worker functions ───────────────────────────────────────

def _worker_help(prompt):
    """Search usekit help system with smart topic mapping."""
    try:
        from usekit.help.use_help import show_help, _get_help_data
        import io, contextlib

        # API name → relevant help topics
        _API_TOPIC_MAP = {
            "wjb": ["examples", "action", "quick"],
            "rjb": ["examples", "action", "keydata", "quick"],
            "ujb": ["examples", "action"],
            "djb": ["examples", "action"],
            "hjb": ["examples", "action"],
            "wjm": ["examples", "action"],
            "rjm": ["examples", "action"],
            "xsb": ["examples", "action"],
            "xdb": ["examples", "action"],
            "ipb": ["examples", "action"],
            "xpb": ["examples", "action"],
        }

        # Keyword → relevant help topics
        _KW_TOPIC_MAP = {
            "append": ["examples", "action"],
            "jsonl":  ["examples", "action"],
            "keydata": ["keydata", "examples"],
            "walk":   ["walk", "examples"],
            "pattern": ["pattern", "examples"],
            "alias":  ["alias"],
            "format": ["object", "alias"],
        }

        # Collect which topics to fetch
        topics_needed = set()

        # From API names in prompt
        u_apis = re.findall(r'u\.(\w+)', prompt)
        for api in u_apis:
            for t in _API_TOPIC_MAP.get(api, ["examples", "quick"]):
                topics_needed.add(t)

        # From keywords
        p = prompt.lower()
        for kw, topics in _KW_TOPIC_MAP.items():
            if kw in p:
                topics_needed.update(topics)

        # Default: at least examples + quick
        if not topics_needed:
            topics_needed = {"examples", "quick"}

        # Fetch matching help topics
        results = []
        for topic in topics_needed:
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    show_help(topic)
                text = buf.getvalue().strip()
                if text and "not found" not in text:
                    results.append(f"[help:{topic}]\n{text[:400]}")
            except Exception:
                pass

        return "\n\n".join(results) if results else ""
    except ImportError:
        return ""


def _worker_docs(prompt):
    """Search docs/ directory for relevant content."""
    try:
        base = _find_base()
        if not base:
            return ""

        # Search keywords from prompt
        keywords = _extract_keywords(prompt)
        if not keywords:
            return ""

        doc_dirs = [
            base / "docs",
            base / ".usekit" / "docs",
        ]

        results = []
        for doc_dir in doc_dirs:
            if not doc_dir.exists():
                continue
            for md in doc_dir.rglob("*.md"):
                try:
                    text = md.read_text(encoding="utf-8", errors="ignore")
                    # Check if any keyword appears
                    t_lower = text.lower()
                    hits = sum(1 for kw in keywords if kw in t_lower)
                    if hits > 0:
                        # Extract relevant section (around first hit)
                        excerpt = _extract_around(text, keywords[0], chars=400)
                        name = md.relative_to(base) if base in md.parents else md.name
                        results.append(f"[docs:{name}]\n{excerpt}")
                except Exception:
                    pass

        return "\n\n".join(results[:5]) if results else ""
    except Exception:
        return ""


def _worker_examples(prompt):
    """Search examples/ directory."""
    try:
        base = _find_base()
        if not base:
            return ""

        keywords = _extract_keywords(prompt)
        if not keywords:
            return ""

        examples_dir = base / "examples"
        if not examples_dir.exists():
            return ""

        results = []
        for py in examples_dir.rglob("*.py"):
            try:
                text = py.read_text(encoding="utf-8", errors="ignore")
                t_lower = text.lower()
                hits = sum(1 for kw in keywords if kw in t_lower)
                if hits > 0:
                    # Take first 600 chars of matching file
                    name = py.relative_to(base)
                    results.append(f"[example:{name}]\n{text[:600]}")
            except Exception:
                pass

        return "\n\n".join(results[:3]) if results else ""
    except Exception:
        return ""


def _worker_source(prompt):
    """Search usekit source code for implementations."""
    try:
        base = _find_base()
        if not base:
            return ""

        keywords = _extract_keywords(prompt)
        if not keywords:
            return ""

        src_dir = base / ".usekit"
        if not src_dir.exists():
            return ""

        results = []
        # Focus on non-pycache python files
        for py in src_dir.rglob("*.py"):
            if "__pycache__" in str(py):
                continue
            try:
                text = py.read_text(encoding="utf-8", errors="ignore")
                t_lower = text.lower()
                # Match function/class definitions containing keywords
                for kw in keywords:
                    if kw in t_lower:
                        # Find the def/class line
                        for i, line in enumerate(text.split("\n")):
                            if kw in line.lower() and (
                                line.strip().startswith("def ") or
                                line.strip().startswith("class ") or
                                f"def {kw}" in line.lower() or
                                f'"{kw}"' in line.lower()
                            ):
                                # Extract surrounding lines
                                lines = text.split("\n")
                                start = max(0, i - 2)
                                end = min(len(lines), i + 15)
                                chunk = "\n".join(lines[start:end])
                                name = py.relative_to(base)
                                results.append(f"[source:{name}:L{i+1}]\n{chunk}")
                                break
            except Exception:
                pass

        return "\n\n".join(results[:5]) if results else ""
    except Exception:
        return ""


# Worker registry
_WORKERS = {
    HELP:     _worker_help,
    DOCS:     _worker_docs,
    EXAMPLES: _worker_examples,
    SOURCE:   _worker_source,
}


# ── Merge (single LLM call) ─────────────────────────────────────

def _merge(handler, prompt, gathered, context=""):
    """
    Merge gathered results via single LLM call.

    Sends all collected data to the connected provider
    and asks it to synthesize a concise answer.
    """
    # Build source block
    source_parts = []
    for g in gathered:
        if g.get("found") and g.get("data"):
            source_parts.append(g["data"])

    if not source_parts:
        result = handler.run(prompt)
        return result.get("text", "")

    sources_text = "\n\n".join(source_parts)

    # Truncate — keep merge prompt compact for speed
    if len(sources_text) > 4000:
        sources_text = sources_text[:4000] + "\n...(truncated)"

    # Load project guide (trimmed for merge)
    guide = ""
    try:
        from usekit.llm.parallel.llp_chat import _load_guide
        raw_guide = _load_guide()
        # Only include Common Patterns + Key Parameters sections
        if raw_guide:
            guide = raw_guide[:1500]
    except Exception:
        pass

    merge_prompt = ""
    if guide:
        merge_prompt += f"PROJECT GUIDE:\n{guide}\n\n"
    merge_prompt += (
        f"사용자 질문: {prompt}\n\n"
        f"아래는 usekit 내부에서 수집한 참고 자료입니다.\n"
        f"이 자료를 바탕으로 정확하고 간결한 답변을 작성하세요.\n"
        f"코드 예제는 실행 가능한 형태로, 모바일 화면에 맞게 짧게.\n"
        f"자료에 없는 내용은 추측하지 마세요.\n\n"
        f"── 수집 자료 ──\n{sources_text}"
    )

    if context:
        merge_prompt = f"대화 맥락:\n{context}\n\n{merge_prompt}"

    result = handler.run(merge_prompt)
    return result.get("text", "")


# ── Gap detection ────────────────────────────────────────────────

def _find_gaps(prompt, gathered):
    """
    Check if gathered results have obvious gaps.

    Returns list of additional source types to search.
    """
    found_sources = {g["source"] for g in gathered if g.get("found")}
    all_sources = {g["source"] for g in gathered}
    missing = all_sources - found_sources

    gaps = []

    # If help found nothing, try docs
    if HELP in missing and DOCS not in all_sources:
        gaps.append(DOCS)

    # If examples found nothing, try source
    if EXAMPLES in missing and SOURCE not in all_sources:
        gaps.append(SOURCE)

    # If source found nothing, try docs
    if SOURCE in missing and DOCS not in all_sources:
        gaps.append(DOCS)

    return gaps


# ── Verify (code execution) ─────────────────────────────────────

def _verify(merged_text):
    """
    Extract code blocks from merged text and execute them.

    Only runs simple, safe-looking code.
    Returns list of {code, result, ok}.
    """
    # Find python code blocks
    blocks = re.findall(r'```python\s*(.*?)```', merged_text, re.S)
    if not blocks:
        # Try indented code
        blocks = re.findall(r'\n((?:    .+\n)+)', merged_text)

    results = []
    for code in blocks[:3]:  # Max 3 blocks
        code = code.strip()
        if not code:
            continue

        # Safety check — skip dangerous patterns
        if any(d in code for d in ["import os", "import sys", "subprocess",
                                    "open(", "exec(", "eval(", "__",
                                    "shutil", "rm ", "del "]):
            continue

        # Only run if it looks like usekit code
        if not any(p in code for p in ["u.", "ua.", "ud.", "uw.", "ut."]):
            continue

        try:
            from usekit import u, ua, ud, uw, ut, s
            ns = {"u": u, "ua": ua, "ud": ud, "uw": uw, "ut": ut, "s": s}

            # Capture output
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                exec(code, ns)
            output = buf.getvalue().strip()

            # Check if last line is an expression
            lines = code.strip().split("\n")
            last = lines[-1].strip()
            if not last.startswith(("print", "import", "from", "def ",
                                     "class ", "if ", "for ", "while ",
                                     "#", "ua.", "u.w", "u.d")):
                try:
                    val = eval(last, ns)
                    if val is not None:
                        output = str(val)
                except Exception:
                    pass

            results.append({
                "code": code[:200],
                "result": output[:300] if output else "(no output)",
                "ok": True,
            })
        except Exception as e:
            results.append({
                "code": code[:200],
                "result": f"Error: {e}",
                "ok": False,
            })

    return results


# ── Utilities ────────────────────────────────────────────────────

def _find_base():
    """Find usekit base/project path."""
    try:
        base = os.getenv("ENV_BASE_PATH") or os.getenv("USEKIT_BASE") or os.getenv("BASE_PATH")
        if base:
            return Path(base)
    except Exception:
        pass

    try:
        from usekit.classes.common.utils.helper_const import get_base_path
        return get_base_path()
    except Exception:
        pass

    return None


def _extract_keywords(prompt):
    """Extract search keywords from prompt."""
    # Remove common words
    stop = {
        "이", "가", "를", "은", "는", "에", "의", "로", "해줘", "해", "줘",
        "알려줘", "보여줘", "설명", "방법", "예제", "example", "how", "to",
        "the", "a", "an", "is", "are", "and", "or", "not", "in", "for",
        "please", "show", "me", "tell", "explain", "what",
    }

    # Extract u.xxx patterns first
    u_apis = re.findall(r'u\.(\w+)', prompt)

    # General words
    words = re.findall(r'[a-zA-Z_]{2,}|[가-힣]{2,}', prompt.lower())
    keywords = [w for w in words if w not in stop and len(w) > 1]

    # API patterns take priority
    return u_apis + keywords


def _extract_around(text, keyword, chars=400):
    """Extract text around first occurrence of keyword."""
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return text[:chars]
    start = max(0, idx - chars // 4)
    end = min(len(text), idx + chars)
    excerpt = text[start:end]
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt = excerpt + "..."
    return excerpt


__all__ = ["dispatch_recall"]
