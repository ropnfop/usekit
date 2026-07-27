# Path: usekit.llm.base.init.lli_prompt.py
# -----------------------------------------------------------------------
#  System prompt templates for structured LLM responses.
#
#  Forces LLM to return {meta, text} format so recv can auto-extract
#  summary, keywords, importance for the feedback loop.
# -----------------------------------------------------------------------

# ── MVP meta format ───────────────────────────────────────────────

_META_INSTRUCTION = """\
Write your full response FIRST, as normal plain text (no JSON, no wrapper).
Then, on a NEW LINE after your response, append exactly one metadata line:

[[META]]{"i": <importance 1-9, 5=neutral>, "kw": ["kw1","kw2"], "s": "<≤50 char summary>"}

Rules:
- Your answer comes first, written naturally. The reader sees only that part.
- The [[META]] line is machine-only metadata, appended once at the very end.
- "i": 1=trivial, 5=normal, 9=critical — how important this is for future context.
- "kw": 2-5 keywords capturing the core topics, in the user's language.
- "s": one-line summary (≤50 chars), same language as the user.
- The [[META]] line must be valid JSON after the marker, all on one line.
- Messages prefixed with [CTX] are past summaries for context only. Do NOT mimic their format."""


def get_system_prompt(base_system: str = "", mode: str = "meta") -> str:
    """
    Build system prompt with meta instruction injected.

    Args:
        base_system: user's custom system prompt (prepended)
        mode: 'meta' = force structured response
              'plain' = no meta injection (raw response)

    Returns:
        Combined system prompt string.
    """
    if mode == "plain":
        return base_system

    parts = []
    if base_system:
        parts.append(base_system)
    parts.append(_META_INSTRUCTION)
    return "\n\n".join(parts)


def get_meta_instruction() -> str:
    """Return the raw meta instruction string (for inspection)."""
    return _META_INSTRUCTION


__all__ = ["get_system_prompt", "get_meta_instruction"]
