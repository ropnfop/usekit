# Path: usekit.llm.base.post.llp_recv.py
# -----------------------------------------------------------------------
#  Unified recv dispatcher — routes to provider-specific parser
# -----------------------------------------------------------------------

from usekit.llm.base.post.parser import parser_openai
from usekit.llm.base.post.parser import parser_gemini
from usekit.llm.base.post.llp_reasoning import split_reasoning

# Parser registry
_PARSERS = {
    "openai":  parser_openai,
    "qwen":    parser_openai,
    "groq":    parser_openai,
    "groq_api": parser_openai,   # official Groq API — same OpenAI-compatible shape
    "openrouter": parser_openai, # OpenRouter unified API — OpenAI-compatible
    "ollama":  parser_openai,
    "vllm":    parser_openai,
    "lmstudio": parser_openai,
    # Gemini now goes through the OpenAI-compat endpoint (adapter=openai in
    # sys_ai.yaml), so its response is OpenAI-shaped → parse with parser_openai.
    # parser_gemini stays in the repo for the native SDK/REST path (future).
    "gemini":  parser_openai,
}


def _with_reasoning(result: dict) -> dict:
    """Split provider reasoning (<think>...) out of `text` into `reasoning`.

    Single choke point for every path (chat/task/REPL/CLI). `text` becomes the
    clean final answer; `reasoning` holds the chain-of-thought (or "").
    """
    if isinstance(result, dict):
        clean, reasoning = split_reasoning(result.get("text", ""))
        result["text"] = clean
        result["reasoning"] = reasoning
    return result


def recv(raw: dict, provider: str = "openai") -> dict:
    """
    Route raw response to the right parser.

    Returns unified result dict:
        text, reasoning, content, usage, elapsed, provider, model,
        status, finish, error, raw
    """
    parser = _PARSERS.get(provider)

    if not parser:
        # fallback: return raw as-is with minimal wrapping
        return _with_reasoning({
            "text": str(raw),
            "content": None,
            "usage": {},
            "elapsed": raw.get("_elapsed", 0) if isinstance(raw, dict) else 0,
            "provider": provider,
            "model": "",
            "status": "unknown",
            "finish": None,
            "error": f"no parser for provider: {provider}",
            "raw": raw,
        })

    return _with_reasoning(parser.parse(raw))
