# Path: usekit.llm.base.post.llp_reasoning.py
# -----------------------------------------------------------------------
#  Reasoning extraction — split provider "thinking" blocks from final text
# -----------------------------------------------------------------------
#  Reasoning-capable models (Qwen, DeepSeek, GPT-OSS, ...) emit their chain
#  of thought wrapped in tags like <think>...</think>. This is the ONE place
#  that knows those formats, so every path (chat/task/REPL/CLI) gets the same
#  clean separation by calling split_reasoning() once in recv().
# -----------------------------------------------------------------------

import re
from typing import Tuple

# Tag pairs that wrap reasoning. Add new variants here only.
# Matched case-insensitively, across newlines, non-greedy.
_REASONING_TAGS = ("think", "thinking", "reasoning", "reflection")

# Build one regex: <(think|thinking|...)> ... </\1>
_TAG_ALT = "|".join(_REASONING_TAGS)
_REASONING_RE = re.compile(
    r"<(?P<tag>" + _TAG_ALT + r")\s*>(?P<body>[\s\S]*?)</(?P=tag)\s*>",
    re.IGNORECASE,
)

# An unclosed leading block: model started <think> but got cut off (max_tokens)
# before the answer. Treat everything after the open tag as reasoning so the
# UI doesn't show a raw dangling <think>.
_OPEN_ONLY_RE = re.compile(
    r"^\s*<(?P<tag>" + _TAG_ALT + r")\s*>(?P<body>[\s\S]*)$",
    re.IGNORECASE,
)


def split_reasoning(text: str) -> Tuple[str, str]:
    """
    Separate reasoning blocks from the final answer.

    Returns (clean_text, reasoning):
      - clean_text: answer with all reasoning blocks removed, trimmed.
      - reasoning:  concatenated reasoning content ("" if none).

    The reasoning is NOT discarded — it is returned so callers can fold/show
    it. Idempotent: running it on already-clean text returns (text, "").
    """
    if not text or not isinstance(text, str):
        return (text or ""), ""

    # Fast path: no reasoning markers at all.
    low = text.lower()
    if not any(("<" + t) in low for t in _REASONING_TAGS):
        return text.strip(), ""

    reasoning_parts = []

    def _capture(m):
        reasoning_parts.append(m.group("body").strip())
        return ""

    clean = _REASONING_RE.sub(_capture, text)

    # Handle a leading open-only block (truncated output) if no closed block
    # consumed it and a dangling open tag remains.
    if not reasoning_parts:
        m = _OPEN_ONLY_RE.match(text)
        if m and ("</" + m.group("tag").lower()) not in low:
            return "", m.group("body").strip()

    reasoning = "\n\n".join(p for p in reasoning_parts if p)
    return clean.strip(), reasoning
