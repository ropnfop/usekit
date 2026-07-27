# Path: usekit.classes.support.base.init.ai.sbi_ai_config.py
# -----------------------------------------------------------------------------------------------
#  Provider config storage — ~/.usekit/llm_providers.json
#
#  Format:
#    {
#        "qwen":   {"base_url": "...", "api_key": "...", "model": "..."},
#        "gemini": {"api_key": "...", "model": "gemini-2.0-flash"},
#        "ollama": {"base_url": "http://localhost:11434/v1", "model": "llama3"}
#    }
#
#  Used by sbi_ai.AIManager — kept as a separate module so the
#  on-disk format is one place to change.
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


# Default config file location: ~/.usekit/llm_providers.json
# Falls back to $USEKIT_CONFIG_DIR/llm_providers.json if env var set.
def _config_path() -> Path:
    base = os.environ.get("USEKIT_CONFIG_DIR")
    root = Path(base) if base else Path.home() / ".usekit"
    return root / "llm_providers.json"


def load_providers() -> Dict[str, Dict[str, Any]]:
    """
    Load full provider config. Returns {} on missing/empty/corrupt file.

    Never raises — config corruption shouldn't crash the system.
    """
    p = _config_path()
    if not p.exists():
        return {}
    try:
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def get_provider(name: str) -> Dict[str, Any]:
    """
    Get config dict for one provider. Returns {} if not configured.

    Example:
        cfg = get_provider("qwen")
        # → {"base_url": "...", "api_key": "...", "model": "..."}
    """
    return load_providers().get(name.lower().strip(), {})


def save_provider(name: str, **fields) -> Dict[str, Any]:
    """
    Merge fields into one provider's config and persist atomically.
    Returns the merged config for that provider.

    Example:
        save_provider("qwen",
            base_url="https://qwen.ai.unturf.com/v1",
            api_key="choose-any-value",
            model="hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
        )
    """
    name = name.lower().strip()
    if not name:
        raise ValueError("[sbi_ai_config] empty provider name")

    all_cfg = load_providers()
    current = dict(all_cfg.get(name, {}))
    # Drop None values so callers can clear a field with =None
    for k, v in fields.items():
        if v is None:
            current.pop(k, None)
        else:
            current[k] = v
    all_cfg[name] = current

    _write_atomic(all_cfg)
    return current


def delete_provider(name: str) -> bool:
    """Remove one provider's config. Returns True if it existed."""
    name = name.lower().strip()
    all_cfg = load_providers()
    if name not in all_cfg:
        return False
    all_cfg.pop(name)
    _write_atomic(all_cfg)
    return True


def list_configured() -> list:
    """Return list of provider names that have stored config."""
    return sorted(load_providers().keys())


# ── Runtime state (health / rate-limit) ─────────────────────────
# Stored under each provider's "_state" key so it never collides with
# user-set fields (base_url/api_key/model). Written by the gateway.
#   _state = {healthy, last_status, last_error, checked_at,
#             consecutive_fails, retry_after_ts}

def get_state(name: str) -> Dict[str, Any]:
    """Get runtime state dict for one provider. Returns {} if none."""
    cfg = get_provider(name)
    st = cfg.get("_state") if isinstance(cfg, dict) else None
    return dict(st) if isinstance(st, dict) else {}


def set_state(name: str, **fields) -> Dict[str, Any]:
    """
    Merge fields into one provider's runtime _state and persist atomically.
    None values clear that field. Returns the merged _state.
    """
    name = name.lower().strip()
    if not name:
        raise ValueError("[sbi_ai_config] empty provider name")

    all_cfg = load_providers()
    current = dict(all_cfg.get(name, {}))
    state = dict(current.get("_state", {}))
    for k, v in fields.items():
        if v is None:
            state.pop(k, None)
        else:
            state[k] = v
    current["_state"] = state
    all_cfg[name] = current

    _write_atomic(all_cfg)
    return state


def config_path() -> str:
    """Return the absolute path to the providers config file."""
    return str(_config_path())


# ── Internal ────────────────────────────────────────────────────

def _write_atomic(data: Dict[str, Any]) -> None:
    """
    Write JSON atomically: write to .tmp then rename.
    Guarantees the file is either fully written or unchanged.
    """
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    payload = json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True)
    tmp.write_text(payload + "\n", encoding="utf-8")
    os.replace(str(tmp), str(p))
    # Best-effort: tighten permissions since this holds API keys.
    try:
        os.chmod(str(p), 0o600)
    except OSError:
        pass


__all__ = [
    "load_providers",
    "get_provider",
    "save_provider",
    "delete_provider",
    "list_configured",
    "get_state",
    "set_state",
    "config_path",
]

# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
