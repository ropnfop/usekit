# Path: usekit.llm.parallel.llp_chat.py
# -----------------------------------------------------------------------
#  ua.chat() — orchestrated dispatch engine
#
#  External:  ua.chat("prompt")
#  Internal:  mode → single / parallel / auto
#
#  single   → existing ua.run()
#  parallel → plan → worker dispatch → assemble
#  auto     → detect from prompt complexity
# -----------------------------------------------------------------------

import json
import re
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# ── Worker limits (Termux-safe) ───────────────────────────────────────

TASK_LIMITS = {
    "search":    {"max_workers": 3, "timeout": 30},
    "analyze":   {"max_workers": 2, "timeout": 45},
    "summarize": {"max_workers": 3, "timeout": 30},
    "draft":     {"max_workers": 1, "timeout": 60},
    "compare":   {"max_workers": 2, "timeout": 45},
}


# ── Assembly priority (source_type → rank) ────────────────────────────

_PRIORITY = {
    "execution_result": 1,
    "local_source":     2,
    "local_docs":       3,
    "local_examples":   4,
    "claude_analysis":  5,
    "qwen_suggestion":  6,
    "web_external":     7,
}


# ── Worker constraint prompt ──────────────────────────────────────────

_CONSTRAINT = (
    "CONSTRAINT: You are a READ-ONLY worker. "
    "You must NOT modify files, run destructive commands, "
    "invent APIs, ignore local docs, execute code, or delete anything."
)


# ── Input size limits ─────────────────────────────────────────────────

_MAX_INPUT = 20_000
_CHUNK_SZ = 8_000


def _chunk(text):
    if len(text.encode("utf-8")) <= _MAX_INPUT:
        return [text]
    chunks, cur, sz = [], [], 0
    for line in text.split("\n"):
        lb = len(line.encode("utf-8")) + 1
        if sz + lb > _CHUNK_SZ and cur:
            chunks.append("\n".join(cur))
            cur, sz = [], 0
        cur.append(line)
        sz += lb
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def _safe_preview(text, limit=1200):
    """Truncate text preserving line/code-block boundaries."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    # Prefer line boundary
    nl = cut.rfind("\n")
    if nl > limit * 0.5:
        cut = cut[:nl]
    # Close unclosed code block
    if cut.count("```") % 2 == 1:
        cut += "\n```"
    cut += "\n...[truncated]"
    return cut


# ══════════════════════════════════════════════════════════════════════
#  dispatch_chat — main entry point (called by ua.chat)
# ══════════════════════════════════════════════════════════════════════

def dispatch_chat(handler, prompt, **kw):
    """
    Route chat to the right execution path.

    Args:
        handler: AIHandler instance (ua)
        prompt:  user prompt string
        **kw:    mode, workers, worker, input_text, input_paths, ...

    Returns:
        dict {text, mode, elapsed, ...}
    """
    mode = kw.pop("mode", None) or handler._config.get("mode", "single")
    workers = kw.pop("workers", None) or handler._config.get("workers", 1)
    worker_prov = kw.pop("worker", None) or handler._config.get("worker")

    if mode == "auto":
        mode = _detect_mode(prompt, workers)

    if mode == "parallel" and workers > 1 and worker_prov:
        return _run_parallel(handler, prompt, worker_prov, workers, **kw)
    return _run_single(handler, prompt, **kw)


# ── Single mode ───────────────────────────────────────────────────────

def _run_single(handler, prompt, **kw):
    t0 = time.time()
    result = handler.run(prompt, **kw)
    return {
        "text": result.get("text", ""),
        "mode": "single",
        "elapsed": round(time.time() - t0, 3),
        "raw": result,
    }


# ── Parallel mode ─────────────────────────────────────────────────────

def _run_parallel(handler, prompt, worker_prov, workers, **kw):
    t0 = time.time()
    input_text = kw.pop("input_text", "")
    input_paths = kw.pop("input_paths", [])

    plan = _plan(handler, prompt, workers)
    if not plan:
        return _run_single(handler, prompt, **kw)

    results = _dispatch(handler, plan, worker_prov, input_text, input_paths)
    final = _assemble(results)

    return {
        "text": final,
        "mode": "parallel",
        "elapsed": round(time.time() - t0, 3),
        "workers_used": len(plan),
        "results": results,
    }


def _plan(handler, prompt, max_w, plan_mode="rule"):
    """
    Decompose prompt into subtasks.

    Modes:
        rule — local keyword heuristic (0ms, no LLM call)
        llm  — ask connected provider to split (slow, costs 1 turn)
    """
    if plan_mode == "llm":
        return _plan_llm(handler, prompt, max_w)
    return _plan_fast(prompt, max_w)


def _plan_fast(prompt, max_w):
    """
    Local heuristic planner — zero LLM calls.

    Detects task keywords in the prompt and generates subtask list.
    Returns [] if prompt is too simple to split.
    """
    p = prompt.lower()

    # Task detection patterns: (signal_words, role, task_type, task_template)
    _PATTERNS = [
        (["분석", "analyze", "검토", "review", "살펴"],
         "analyst", "analyze", "분석: {prompt}"),
        (["버그", "bug", "오류", "에러", "error", "문제점", "찾아"],
         "debugger", "analyze", "버그/오류 탐색: {prompt}"),
        (["문서", "doc", "작성", "write", "draft", "초안", "정리"],
         "writer", "draft", "문서 작성/정리: {prompt}"),
        (["비교", "compare", "차이", "differ", "vs"],
         "comparator", "compare", "비교 분석: {prompt}"),
        (["요약", "summar", "정리해", "핵심"],
         "summarizer", "summarize", "요약: {prompt}"),
        (["검색", "search", "찾아", "find", "조사"],
         "researcher", "search", "조사/검색: {prompt}"),
        (["개선", "improve", "최적", "optim", "리팩"],
         "optimizer", "analyze", "개선 방안: {prompt}"),
        (["테스트", "test", "검증", "verif"],
         "tester", "analyze", "테스트/검증: {prompt}"),
    ]

    matched = []
    seen_types = set()
    for signals, role, ttype, template in _PATTERNS:
        if any(s in p for s in signals):
            # Avoid duplicate task_types unless different role
            key = f"{role}_{ttype}"
            if key not in seen_types:
                seen_types.add(key)
                matched.append({
                    "role": role,
                    "task_type": ttype,
                    "task": template.format(prompt=prompt[:200]),
                })

    if len(matched) < 2:
        # Not enough diversity to parallelize
        return []

    return matched[:max_w]


def _default_analysis_plan(prompt, max_w):
    """
    Default plan when input_text exists but _plan_fast found < 2 keywords.

    Generates analyst + debugger + researcher roles for general code analysis.
    """
    roles = [
        {"role": "analyst",    "task_type": "analyze", "task": f"분석: {prompt[:200]}"},
        {"role": "debugger",   "task_type": "analyze", "task": f"버그/오류 탐색: {prompt[:200]}"},
        {"role": "researcher", "task_type": "search",  "task": f"조사/검색: {prompt[:200]}"},
    ]
    return roles[:max_w]


def _plan_llm(handler, prompt, max_w):
    """Ask connected provider to decompose prompt into subtasks (original)."""
    plan_prompt = (
        f"Split this into {max_w} independent subtasks.\n\n"
        f"REQUEST: {prompt}\n\n"
        f"RESPOND JSON only — list of {{role, task_type, task}}.\n"
        f"Valid task_type: search, analyze, summarize, draft, compare.\n"
        f"If too simple to split, return []."
    )
    try:
        r = handler.run(plan_prompt)
        text = r.get("text", "")
        clean = re.sub(r'```json\s*|```\s*', '', text)
        m = re.search(r'\[[\s\S]*\]', clean)
        if m:
            plan = json.loads(m.group())
            if isinstance(plan, list) and plan:
                return plan[:max_w]
    except Exception:
        pass
    return []


def _dispatch(handler, plan, worker_prov, input_text, input_paths):
    """Run subtasks via gateway.dispatch_one in ThreadPoolExecutor."""
    from usekit.classes.support.base.init.ai import sbi_ai_gateway as _gw

    chunks = _chunk(input_text) if input_text else [""]
    by_type = {}
    for item in plan:
        by_type.setdefault(item.get("task_type", "search"), []).append(item)

    all_results = []

    for tt, items in by_type.items():
        lim = TASK_LIMITS.get(tt, {"max_workers": 2, "timeout": 60})
        mw = min(lim["max_workers"], len(items))

        with ThreadPoolExecutor(max_workers=mw) as pool:
            futures = {}
            for item in items:
                wp = _worker_prompt(item, chunks[0], input_paths)
                jid = f"{tt}_{uuid.uuid4().hex[:8]}"
                f = pool.submit(
                    _gw.dispatch_one,
                    worker_prov,
                    wp,
                    timeout=lim["timeout"],
                )
                futures[f] = {"job_id": jid, **item}

            for f in as_completed(futures):
                meta = futures[f]
                try:
                    raw = f.result(timeout=lim["timeout"] + 10)
                    all_results.append(_parse(raw, meta))
                except Exception as e:
                    all_results.append(_err(meta, str(e)))

    return all_results


def _worker_prompt(item, input_text, input_paths):
    """Build constrained prompt for read-only worker."""
    parts = [
        f"ROLE: {item.get('role', 'worker')}",
        "PERMISSION: read_only",
        _CONSTRAINT,
    ]
    guide = _load_guide()
    if guide:
        parts.append(f"\nPROJECT GUIDE:\n{guide}")
    parts.append(f"\nTASK: {item.get('task', '')}")
    if input_text:
        parts.append(f"\nINPUT:\n{input_text}")
    if input_paths:
        parts.append(f"\nPATHS: {', '.join(input_paths)}")
    parts.append(
        "\nRESPOND JSON only. Fields: status, confidence (0-1), "
        "source_type, summary, key_points, evidence, risks, suggestions."
    )
    return "\n".join(parts)


def _parse(raw, meta):
    """Parse serve_chat response → structured result."""
    text = raw.get("text", "") if isinstance(raw, dict) else str(raw)
    parsed = {}
    try:
        clean = re.sub(r'```json\s*|```\s*', '', text)
        m = re.search(r'\{[\s\S]*\}', clean)
        if m:
            parsed = json.loads(m.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return {
        "job_id": meta.get("job_id", ""),
        "role": meta.get("role", "worker"),
        "status": parsed.get("status", "ok" if raw.get("ok") else "error"),
        "confidence": parsed.get("confidence", 0.5),
        "source_type": parsed.get("source_type", "qwen_suggestion"),
        "summary": parsed.get("summary", _safe_preview(text)),
        "key_points": parsed.get("key_points", []),
        "evidence": parsed.get("evidence", []),
        "risks": parsed.get("risks", []),
        "suggestions": parsed.get("suggestions", []),
        "elapsed": raw.get("elapsed", 0),
        # transport-level signals (propagated for judge / recirculation guard)
        "fatal": bool(raw.get("fatal")) if isinstance(raw, dict) else False,
        "status_code": raw.get("status_code") if isinstance(raw, dict) else None,
        "retry_after": raw.get("retry_after") if isinstance(raw, dict) else None,
        "error": raw.get("error") if isinstance(raw, dict) else None,
    }


def _err(meta, msg):
    return {
        "job_id": meta.get("job_id", ""),
        "role": meta.get("role", "worker"),
        "status": "error",
        "confidence": 0.0,
        "source_type": "none",
        "summary": f"Error: {msg}",
        "key_points": [],
        "evidence": [],
        "risks": [msg],
        "suggestions": [],
        "elapsed": 0,
    }


# ── Assembly ──────────────────────────────────────────────────────────

def _any_fatal(results):
    """True if any worker result is a fatal transport error (429/5xx)."""
    return any(isinstance(r, dict) and r.get("fatal") for r in (results or []))


def _first_fatal(results):
    """Return the first fatal result dict, or None."""
    for r in (results or []):
        if isinstance(r, dict) and r.get("fatal"):
            return r
    return None


def _assemble(results):
    """
    Combine worker results — semantic dedup, prioritized suggestions.

    For parallel: merge summaries, deduplicate by meaning, classify fixes.
    For recall: pass through summary directly.
    """
    if not results:
        return "(no worker results)"

    # All-pending detection
    active = [r for r in results if r.get("status") not in ("error",)]
    if active and all(r.get("status") == "pending" for r in active):
        roles = ", ".join(r.get("role", "?") for r in active)
        return (
            f"[parallel] {len(active)}개 worker({roles})가 모두 대기 상태입니다.\n"
            f"분석 대상이 필요합니다. input_text= 파라미터로 코드나 텍스트를 전달해주세요.\n"
            f"예: ua.chat('분석해줘', mode='parallel', worker='qwen', workers=3, input_text=코드)"
        )

    # Single recall result → pass through
    if len(active) == 1 and active[0].get("role") == "recall":
        return active[0].get("summary", "")

    # Filter OK results, sort by confidence desc
    ok = [r for r in active if r.get("status") not in ("error", "pending")]
    ok.sort(key=lambda r: r.get("confidence", 0), reverse=True)

    if not ok:
        return "(all workers failed)"

    # Summary — highest confidence
    summary = ok[0].get("summary", "")

    # Semantic dedup for key_points
    points = _dedup_semantic(_collect(ok, "key_points"), max_items=4)

    # Semantic dedup for risks
    risks = _dedup_semantic(_collect(ok, "risks"), max_items=3)

    # Classify suggestions into primary / alternative / optional
    all_sugs = _collect(ok, "suggestions")
    primary, alternative, optional = _classify_suggestions(all_sugs)

    # Build user-facing text
    lines = []
    if summary:
        lines.append(summary)
        lines.append("")

    if points:
        for p in points:
            lines.append(f"- {p}")
        lines.append("")

    if risks:
        for rk in risks:
            lines.append(f"  ! {rk}")
        lines.append("")

    if primary:
        lines.append("fix:")
        for s in primary[:2]:
            lines.append(f"  → {s}")

    if alternative:
        lines.append("alt:")
        for s in alternative[:2]:
            lines.append(f"  → {s}")

    if optional:
        lines.append("opt:")
        for s in optional[:2]:
            lines.append(f"  → {s}")

    return "\n".join(lines) if lines else summary


def _collect(results, field):
    """Collect all items from a field across results."""
    items = []
    for r in results:
        items.extend(r.get(field, []))
    return items


def _dedup_semantic(items, max_items=5):
    """
    Remove semantically similar items using word overlap.

    Keeps the longer (more specific) item when duplicates found.
    Threshold: 50% of the larger set overlaps.
    """
    if not items:
        return []

    def _norm(text):
        return " ".join(text.lower().replace("`", "").replace("'", "").replace('"', '').split())

    def _words(text):
        return set(_norm(text).split())

    kept = []
    kept_words = []
    for item in items:
        ws = _words(item)
        if not ws:
            continue
        is_dup = False
        for i, kw in enumerate(kept_words):
            if not kw:
                continue
            overlap = len(ws & kw) / max(len(ws), len(kw))
            if overlap > 0.5:
                # Keep the longer (more specific) one
                if len(item) > len(kept[i]):
                    kept[i] = item
                    kept_words[i] = ws
                is_dup = True
                break
        if not is_dup:
            kept.append(item)
            kept_words.append(ws)
        if len(kept) >= max_items:
            break

    return kept


def _classify_suggestions(suggestions):
    """
    Classify suggestions by intent, not by specific code content.

    fix: direct code change (change, fix, replace, correct, update)
    alt: alternative approach (rename, if intended, alternatively)
    opt: supplementary improvement (test, validation, docstring, type)
    """
    # Normalize + dedup
    seen = set()
    unique = []
    for s in suggestions:
        norm = " ".join(s.lower().replace("`", "").replace("'", "").split())
        if norm not in seen:
            seen.add(norm)
            unique.append(s)

    # Semantic dedup across suggestions
    unique = _dedup_semantic(unique, max_items=8)

    primary, alternative, optional = [], [], []

    for s in unique:
        cat = _classify_one(s)
        if cat == "fix":
            primary.append(s)
        elif cat == "alt":
            alternative.append(s)
        else:
            optional.append(s)

    return primary[:2], alternative[:2], optional[:3]


def _classify_one(s):
    """Classify a single suggestion by intent keywords."""
    x = s.lower()

    # Direct fix — change, fix, replace, correct, update implementation
    if any(w in x for w in ["change", "fix", "replace", "correct", "update"]):
        # But "rename" + "if" = alternative, not fix
        if "rename" in x:
            return "alt"
        return "fix"

    # Alternative — rename, if intended, alternatively, if meant, consider renaming
    if any(w in x for w in ["rename", "alternative", "if intended", "if meant", "consider"]):
        return "alt"

    # Optional — test, validation, docstring, type, logging, comment, verify
    if any(w in x for w in ["test", "validation", "docstring", "type", "logging", "comment", "verify"]):
        return "opt"

    return "opt"


# ── Final Judge (editor LLM pass) ─────────────────────────────────

def _final_judge(handler, prompt, draft, results):
    """
    Final editor pass — one LLM call to produce clean user-facing answer.

    Takes the draft assembly + raw worker results and rewrites into
    a concise, deduplicated, properly structured answer.

    Falls back to draft if LLM call fails.
    """
    # Collect raw material for the editor
    all_suggestions = _collect(
        [r for r in results if r.get("status") not in ("error", "pending")],
        "suggestions"
    )
    all_evidence = _collect(
        [r for r in results if r.get("status") not in ("error", "pending")],
        "evidence"
    )

    editor_prompt = (
        "You are the FINAL EDITOR. Rewrite the draft into a clean answer.\n\n"
        "RULES:\n"
        "- Remove ALL duplicate points\n"
        "- Bullet points describe the PROBLEM only (what is wrong, what code does)\n"
        "- Solutions go ONLY in fix/alt/opt sections — NEVER in bullet points\n"
        "- Keep it SHORT — mobile-friendly, under 12 lines total\n"
        "- Use backticks for code references\n"
        "- Do NOT add new analysis — only reorganize what workers found\n"
        "- Output plain text only, no JSON, no markdown headers\n\n"
        "CLASSIFICATION (strict):\n"
        "  fix: direct code change (change return, fix logic, replace value)\n"
        "  alt: completely different approach IF intent differs (rename function)\n"
        "  opt: supplementary — ALWAYS opt for: validation, unit test, docstring, type hint\n"
        "  ※ validation is NEVER alt. tests are NEVER fix.\n\n"
        "FORMAT (follow exactly):\n"
        "[one-line summary]\n\n"
        "- [what is wrong — problem description]\n"
        "- [what code currently does]\n\n"
        "fix:\n"
        "  → [direct code fix]\n"
        "alt:\n"
        "  → [alternative if intent differs]\n"
        "opt:\n"
        "  → [supplementary improvement]\n\n"
        f"USER QUESTION: {prompt}\n\n"
        f"DRAFT:\n{draft}\n\n"
        f"WORKER SUGGESTIONS:\n"
        + "\n".join(f"- {s}" for s in all_suggestions[:10])
    )

    if all_evidence:
        editor_prompt += (
            f"\n\nEVIDENCE:\n"
            + "\n".join(f"- {e}" if isinstance(e, str) else f"- {e}" for e in all_evidence[:6])
        )

    try:
        result = handler.run(editor_prompt)
        text = result.get("text", "").strip()
        # Sanity check — if editor returned something reasonable
        if text and len(text) > 20:
            return text
    except Exception:
        pass

    # Fallback to rule-based draft
    return draft


# ── Auto mode detection ───────────────────────────────────────────────

def _detect_mode(prompt, workers):
    """Heuristic: complex or multi-step prompts → parallel."""
    signals = [
        "and also", "then", "additionally", "multiple",
        "compare", "each", "보강", "분석", "비교", "각각",
    ]
    has_multi = any(s in prompt.lower() for s in signals)
    if workers > 1 and (len(prompt.split()) > 30 or has_multi):
        return "parallel"
    return "single"


# ══════════════════════════════════════════════════════════════════════
#  dispatch_parallel — history-aware entry (called by ua.chat)
# ══════════════════════════════════════════════════════════════════════

def dispatch_parallel(handler, prompt, worker_prov, max_workers=3, context="", **kw):
    """
    Parallel dispatch with optional recirculation loop.

    Flow:
        plan → dispatch workers → assemble → judge
        → (if gap found) followup workers → final merge

    Args:
        handler:     AIHandler instance (ua)
        prompt:      user prompt
        worker_prov: provider name for workers (e.g. "qwen")
        max_workers: max concurrent workers
        context:     compressed history context string
        on_status:   callback(stage, msg, extra) for progress reporting
        **kw:        input_text, input_paths, recirculate, ...

    Returns:
        {text, mode, workers_used, results, judge, recirculated, rounds, elapsed}
    """
    t0 = time.time()
    input_text = kw.pop("input_text", "")
    input_paths = kw.pop("input_paths", [])
    plan_mode = kw.pop("planner", None) or kw.pop("plan", "rule")  # "rule" | "llm"
    recirculate = kw.pop("recirculate", False)
    max_rounds = kw.pop("max_rounds", 2)
    quality = kw.pop("quality", "review")
    on_status = kw.pop("on_status", None)

    def _emit(stage, msg, **extra):
        if on_status:
            try:
                on_status(stage, msg, extra)
            except Exception:
                pass

    # [1] Plan subtasks
    _emit("plan", "작업 분할 중...")
    plan = _plan(handler, prompt, max_workers, plan_mode=plan_mode)

    # [1.1] Auto-plan: if input_text provided but plan too small, generate default analysis roles
    if len(plan) < 2 and input_text:
        plan = _default_analysis_plan(prompt, max_workers)

    if not plan:
        # No parallel plan — check if recall can handle it
        if recirculate:
            _emit("judge", "판단 중...")
            judge = _judge_results(prompt, [])
            if judge.get("need_recirculation") and "recall" in judge.get("followup_tasks", []):
                _emit("recall", "usekit 내부 검색 중...")
                recall_results = _recirculate_recall(handler, prompt, context)
                if recall_results and recall_results[0].get("status") != "error":
                    _emit("assemble", "결과 조립 중...")
                    final = _assemble(recall_results)
                    return {
                        "text": final,
                        "mode": "recall",
                        "workers_used": len(recall_results),
                        "results": recall_results,
                        "judge": judge,
                        "recirculated": True,
                        "rounds": 1,
                        "elapsed": round(time.time() - t0, 3),
                    }

        # True fallback — single LLM call
        _emit("route", "단일 모드 fallback")
        result = handler.run(prompt)
        return {
            "text": result.get("text", ""),
            "mode": "parallel_fallback",
            "workers_used": 0,
            "results": [],
            "judge": {"need_recirculation": False},
            "recirculated": False,
            "rounds": 1,
            "elapsed": round(time.time() - t0, 3),
        }

    # [1.5] Input warning for analysis tasks
    has_analysis = any(
        t.get("task_type") in ("analyze", "compare") for t in plan
    )
    input_warning = ""
    if has_analysis and not input_text and not input_paths:
        input_warning = (
            "[⚠ input_text 없음] 분석 대상 코드/텍스트가 없어 worker 품질이 제한됩니다.\n"
            "input_text= 파라미터로 분석 대상을 전달하세요.\n\n"
        )

    # [2] Round 1 — dispatch workers
    roles_str = ", ".join(t.get("role", "?") for t in plan)
    _emit("worker", f"worker 분석 중... ({roles_str})", workers=len(plan), roles=roles_str)
    results = _dispatch_with_context(
        handler, plan, worker_prov, input_text, input_paths, context,
        on_status=on_status,
    )

    # [2.5] Fatal guard — if any worker hit a fatal transport error (429/5xx),
    # stop here. Recirculating would just hammer a rate-limited/down provider.
    fr = _first_fatal(results)
    if fr is not None:
        _emit("error", f"provider 오류 — 중단 ({fr.get('error', 'fatal')})")
        return {
            "text": f"[provider 오류] {fr.get('error', 'fatal error')}",
            "mode": "aborted",
            "ok": False,
            "fatal": True,
            "status_code": fr.get("status_code"),
            "retry_after": fr.get("retry_after"),
            "workers_used": len(plan),
            "results": results,
            "judge": {"need_recirculation": False, "reason": "fatal"},
            "recirculated": False,
            "rounds": 1,
            "elapsed": round(time.time() - t0, 3),
        }

    # [3] Judge — decide if recirculation needed
    _emit("judge", "결과 판단 중...")
    judge = _judge_results(prompt, results)
    did_recirculate = False
    round_count = 1

    if recirculate and judge["need_recirculation"] and round_count < max_rounds:
        # [4] Recirculation — handle by type
        round_count += 1
        did_recirculate = True

        followups = judge.get("followup_tasks", [])

        if "recall" in followups:
            # usekit internal query → delegate to recall engine
            _emit("recall", "usekit 내부 검색 중...")
            recall_results = _recirculate_recall(handler, prompt, context)
            if recall_results:
                results.extend(recall_results)
        else:
            # Low confidence / incomplete → re-dispatch with refined plan
            _emit("worker", "보강 분석 중...", round=2)
            followup_plan = _plan_followup(prompt, results, judge, max_workers)
            if followup_plan:
                r2 = _dispatch_with_context(
                    handler, followup_plan, worker_prov,
                    input_text, input_paths, context,
                    on_status=on_status,
                )
                results.extend(r2)

    # [5] Collect → draft
    _emit("assemble", "결과 조립 중...")
    draft = _assemble(results)
    if input_warning:
        draft = input_warning + draft

    # [6] Final judge — quality modes
    #   fast:   skip final judge, use rule-based draft
    #   normal: use rule-based draft (same as fast for now)
    #   review: LLM editor pass for polished output
    if quality == "review":
        _emit("final_judge", "최종 정리 중...")
        final = _final_judge(handler, prompt, draft, results)
    else:
        final = draft

    return {
        "text": final,
        "mode": "parallel",
        "quality": quality,
        "workers_used": len(plan),
        "results": results,
        "judge": judge,
        "recirculated": did_recirculate,
        "rounds": round_count,
        "elapsed": round(time.time() - t0, 3),
    }


# ── Judge (rule-based) ───────────────────────────────────────────

def _judge_results(prompt, results):
    """
    Rule-based judge — decide if recirculation is needed.

    Checks: usekit query, low confidence, incomplete status.
    """
    p = prompt.lower()

    # usekit API query → needs internal recall
    usekit_query = any(s in p for s in ["u.", "usekit", "use.", "ua.", "ud.", "uw.", "ut."])
    if usekit_query:
        return {
            "need_recirculation": True,
            "reason": "usekit query requires internal recall",
            "followup_tasks": ["recall"],
        }

    # Low confidence
    confs = [r.get("confidence", 0.5) for r in results if r.get("status") != "error"]
    avg_conf = sum(confs) / len(confs) if confs else 0
    if avg_conf < 0.6:
        return {
            "need_recirculation": True,
            "reason": f"avg confidence {avg_conf:.2f} < 0.6",
            "followup_tasks": ["clarify", "research"],
        }

    # Incomplete / pending status
    incomplete = any(
        r.get("status") in ("incomplete", "pending") for r in results
    )
    if incomplete:
        return {
            "need_recirculation": True,
            "reason": "worker returned incomplete/pending",
            "followup_tasks": ["verify", "research"],
        }

    return {"need_recirculation": False, "reason": "ok"}


# ── Recirculation helpers ─────────────────────────────────────────

def _recirculate_recall(handler, prompt, context):
    """
    Recirculate via recall engine — fetch usekit internal sources.

    Returns list of structured results compatible with _assemble().
    """
    try:
        from usekit.llm.parallel.llp_recall import dispatch_recall
        recall = dispatch_recall(handler, prompt, context=context)

        if recall.get("mode") == "recall_skip" or not recall.get("text"):
            return []

        return [{
            "job_id": "recall_0",
            "role": "recall",
            "status": "ok",
            "confidence": 0.85,
            "source_type": "local_docs",
            "summary": _safe_preview(recall["text"], 2000),
            "key_points": [f"source: {s}" for s in recall.get("sources", [])],
            "evidence": [],
            "risks": [],
            "suggestions": [],
            "elapsed": recall.get("elapsed", 0),
        }]
    except Exception as e:
        return [{
            "job_id": "recall_err",
            "role": "recall",
            "status": "error",
            "confidence": 0.0,
            "source_type": "none",
            "summary": f"recall error: {e}",
            "key_points": [],
            "evidence": [],
            "risks": [str(e)],
            "suggestions": [],
            "elapsed": 0,
        }]


def _plan_followup(prompt, first_results, judge, max_workers):
    """
    Generate followup plan from judge analysis.

    Uses gaps in first round to create targeted subtasks.
    """
    followups = judge.get("followup_tasks", [])
    reason = judge.get("reason", "")

    plan = []
    for ft in followups[:max_workers]:
        if ft == "clarify":
            plan.append({
                "role": "clarifier",
                "task_type": "analyze",
                "task": f"이전 분석이 불충분({reason}). 재분석: {prompt[:200]}",
            })
        elif ft == "research":
            plan.append({
                "role": "researcher",
                "task_type": "search",
                "task": f"추가 조사 필요({reason}). 검색: {prompt[:200]}",
            })
        elif ft == "verify":
            plan.append({
                "role": "verifier",
                "task_type": "analyze",
                "task": f"이전 결과 검증({reason}). 검증: {prompt[:200]}",
            })

    return plan if plan else None


def _dispatch_with_context(handler, plan, worker_prov, input_text, input_paths, context, on_status=None):
    """
    Run ALL subtasks in a single thread pool — true parallel.

    Each worker goes through gateway.dispatch_one() so health gate,
    fatal(429/5xx) handling, state recording, and the worker concurrency
    semaphore all apply uniformly. Provider config (base_url/key/model) is
    resolved inside the gateway/adapter — not passed here.
    """
    from usekit.classes.support.base.init.ai import sbi_ai_gateway as _gw

    chunks = _chunk(input_text) if input_text else [""]
    timeout = 60  # single timeout for all workers

    all_results = []
    mw = min(len(plan), 4)  # pool size; real concurrency is bounded by gateway semaphore
    total = len(plan)
    done_count = [0]  # mutable for closure

    def _emit(stage, msg, **extra):
        if on_status:
            try:
                on_status(stage, msg, extra)
            except Exception:
                pass

    def _run_worker(wp):
        # dispatch_one returns the standard gateway result dict
        # {ok, text, status_code, fatal, retry_after, error, ...}
        return _gw.dispatch_one(worker_prov, wp, timeout=timeout)

    with ThreadPoolExecutor(max_workers=mw) as pool:
        futures = {}
        for item in plan:
            wp = _worker_prompt_ctx(item, chunks[0], input_paths, context)
            tt = item.get("task_type", "search")
            jid = f"{tt}_{uuid.uuid4().hex[:8]}"
            f = pool.submit(_run_worker, wp)
            futures[f] = {"job_id": jid, **item}

        for f in as_completed(futures):
            meta = futures[f]
            try:
                raw = f.result(timeout=timeout + 10)
                all_results.append(_parse(raw, meta))
            except Exception as e:
                all_results.append(_err(meta, str(e)))
            done_count[0] += 1
            role = meta.get("role", "worker")
            _emit("worker_done", f"{role} 완료 ({done_count[0]}/{total})",
                  progress=f"{done_count[0]}/{total}", role=role)

    return all_results


def _worker_send(prompt, base_url, model, api_key, timeout=60):
    """
    DEPRECATED — no longer called. Workers now route through
    gateway.dispatch_one() (health/fatal/state/semaphore unified).
    Kept temporarily for reference; safe to remove after G2 verification.

    Thread-safe direct REST call to OpenAI-compatible endpoint.

    No singleton state — each call is fully independent.
    Returns same shape as serve_chat: {ok, text, elapsed, ...}
    """
    import requests as req

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1200,
        "stream": False,
    }

    started = time.time()
    try:
        resp = req.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=body,
            timeout=(10, timeout),
        )
        elapsed = round(time.time() - started, 3)
        sc = resp.status_code

        # Non-200 → error. Do NOT return the body as text (it would be
        # mistaken for a low-quality answer and trigger recirculation).
        # 429 / 5xx are 'fatal': retrying or recirculating is pointless.
        if sc != 200:
            retry_after = None
            try:
                ra = resp.headers.get("retry-after")
                if ra is not None:
                    retry_after = float(ra)
            except (TypeError, ValueError):
                retry_after = None
            fatal = sc == 429 or 500 <= sc < 600
            err_msg = f"HTTP {sc}"
            try:
                # surface provider error message for logs, not as answer text
                j = resp.json()
                if isinstance(j, dict) and j.get("error"):
                    e = j["error"]
                    err_msg = f"HTTP {sc}: " + (e.get("message") if isinstance(e, dict) else str(e))
            except Exception:
                pass
            return {
                "ok": False,
                "text": "",
                "error": err_msg,
                "status_code": sc,
                "fatal": fatal,
                "retry_after": retry_after,
                "elapsed": elapsed,
            }

        data = resp.json()

        # Some free proxies (g4f.space) return HTTP 200 with an error body
        # ({"error": {...rate_limit_exceeded...}}) instead of 429. Treat that
        # as a fatal quota error, not as answer text — otherwise str(data) would
        # be injected as a bogus "answer" and recirculated.
        if isinstance(data, dict) and data.get("error"):
            e = data["error"]
            etype = (e.get("type") if isinstance(e, dict) else "") or ""
            emsg = (e.get("message") if isinstance(e, dict) else str(e)) or ""
            is_quota = ("rate_limit" in etype.lower()) or ("limit" in emsg.lower())
            ra = e.get("retry_after") if isinstance(e, dict) else None
            return {
                "ok": False,
                "text": "",
                "error": f"provider error: {emsg}",
                "status_code": sc,
                "fatal": True,
                "quota": is_quota,
                "retry_after": ra,
                "elapsed": elapsed,
            }

        # Extract text from OpenAI format
        text = ""
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            text = str(data)

        return {
            "ok": True,
            "text": text,
            "status_code": sc,
            "elapsed": elapsed,
        }
    except req.Timeout as e:
        # timeout is not fatal (provider may be alive but slow) but must not recirculate blindly
        return {
            "ok": False,
            "text": "",
            "error": f"timeout: {e}",
            "status_code": None,
            "fatal": False,
            "elapsed": round(time.time() - started, 3),
        }
    except Exception as e:
        return {
            "ok": False,
            "text": "",
            "error": str(e),
            "status_code": None,
            "fatal": False,
            "elapsed": round(time.time() - started, 3),
        }


# ── Project guide (CLAUDE.md) cache ──────────────────────────────

_guide_cache = None

# Flag: only inject CLAUDE.md when explicitly opted in.
# Set to True via declare_guide() or ua.set(use_guide=True).
# Default is False — no auto-injection on every call.
_guide_enabled = False

# Flag: when a General USEKIT Project (project_meta) connection is active, the
# project identity lives in the system prompt, so the LLM.md/CLAUDE.md guide is
# suppressed at the source — covering fast, parallel, and recall paths at once
# (avoids double-injecting a competing guide; was the SRS NOTE leak).
_guide_suppressed = False


def suppress_guide(suppressed: bool = True) -> None:
    """Suppress _load_guide() process-wide (set by conn(project_meta=...))."""
    global _guide_suppressed
    _guide_suppressed = suppressed


def declare_guide(enabled: bool = True) -> None:
    """
    Opt-in to CLAUDE.md injection for this process session.

    Call once at startup — not per-request.
    Editor startup: declare_guide(True)
    Default (all other contexts): stays False, never call this.
    """
    global _guide_enabled
    _guide_enabled = enabled


def _load_guide(force: bool = False) -> str:
    """
    Load project AI guide for LLM context.

    Search order (both opt-in via declare_guide(True) or force):
      1. LLM.md  — lightweight project guide
      2. CLAUDE.md — full dev guide

    Neither is loaded by default. USEKIT is a generic toolkit; a project
    guide is an OPTION the project explicitly turns on, never a default,
    so generic chat never leaks project context (SRS NOTE leak fix).

    Returns empty string when nothing found / not opted in, or when
    suppressed by a General USEKIT Project (project_meta) connection.
    """
    global _guide_cache

    # project_meta active → identity is in the system prompt; no guide.
    if _guide_suppressed:
        return ""

    if _guide_cache is not None:
        return _guide_cache

    import os
    from pathlib import Path

    # Resolve project root paths
    roots = []
    base = os.getenv("ENV_BASE_PATH") or os.getenv("USEKIT_BASE") or os.getenv("BASE_PATH")
    if base:
        roots.append(Path(base))
    try:
        from usekit.classes.common.utils.helper_const import get_base_path
        bp = get_base_path()
        if bp:
            roots.append(Path(str(bp)))
    except Exception:
        pass

    # [1] LLM.md — opt-in only (declare_guide(True) or force). USEKIT is a generic
    # toolkit: a project guide is an OPTION the project turns on, never a default.
    # Without opt-in NO project context leaks into generic chat (SRS NOTE leak fix).
    if _guide_enabled or force:
        for root in roots:
            p = root / "LLM.md"
            try:
                if p.exists():
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    if len(text) > 3000:
                        text = text[:3000] + "\n...(trimmed)"
                    _guide_cache = text
                    return _guide_cache
            except Exception:
                pass

    # [2] CLAUDE.md — only when explicitly declared (editor/dev mode)
    if _guide_enabled or force:
        for root in roots:
            p = root / "CLAUDE.md"
            try:
                if p.exists():
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    if len(text) > 3000:
                        text = text[:3000] + "\n...(trimmed)"
                    _guide_cache = text
                    return _guide_cache
            except Exception:
                pass

    _guide_cache = ""
    return _guide_cache


def _worker_prompt_ctx(item, input_text, input_paths, context):
    """Build constrained prompt for worker — with project guide + context."""
    parts = [
        f"ROLE: {item.get('role', 'worker')}",
        "PERMISSION: read_only",
        _CONSTRAINT,
    ]
    # Inject project guide (CLAUDE.md)
    guide = _load_guide()
    if guide:
        parts.append(f"\nPROJECT GUIDE:\n{guide}")
    if context:
        parts.append(f"\nCONVERSATION CONTEXT:\n{context}")
    parts.append(f"\nTASK: {item.get('task', '')}")
    if input_text:
        parts.append(f"\nINPUT:\n{input_text}")
    if input_paths:
        parts.append(f"\nPATHS: {', '.join(input_paths)}")
    parts.append(
        "\nRESPOND JSON only. Fields: status, confidence (0-1), "
        "source_type, summary, key_points, evidence, risks, suggestions."
    )
    return "\n".join(parts)


__all__ = ["dispatch_parallel", "declare_guide", "_load_guide"]
