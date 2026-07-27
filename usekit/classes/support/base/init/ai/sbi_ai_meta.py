# Path: usekit.classes.support.base.init.ai.sbi_ai_meta.py
# -----------------------------------------------------------------------------------------------
#  AI registry resolver — reads sys_ai.yaml, caches, resolves aliases.
#
#  Path resolution mirrors helper_const._get_sys_const_path() so it works in:
#    1. ENV_SYS_AI_PATH override
#    2. Installed package (pip)
#    3. Development BASE_PATH
#
#  Public API:
#    all_meta()            → full yaml dict (UI consumes this via /api/ai_meta)
#    providers()           → dict of provider entries
#    provider_of(alias)    → which provider owns this model alias?
#    resolve_model(alias)  → full model name (e.g. 'G20F' → 'gemini-2.0-flash')
#    adapter_of(provider)  → ua adapter name ('openai'/'gemini'/'anthropic'/'')
#    default_provider()    → first-boot fallback provider name
#    default_model(prov)   → that provider's default alias
#    enabled_providers()   → list of enabled provider names
#    clear_cache()         → drop cache (called by /api/reload_usekit)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Path resolution (mirrors helper_const pattern) ──────────────────

def _yaml_path() -> Path:
    """
    Resolve sys_ai.yaml location:
      1. ENV_SYS_AI_PATH (file or directory)
      2. Package-relative (works in pip install)
      3. BASE_PATH / usekit/sys/sys_yaml/sys_ai.yaml
    """
    env_path = os.getenv("ENV_SYS_AI_PATH") or ""
    if env_path:
        p = Path(env_path)
        return p / "sys_ai.yaml" if p.is_dir() else p

    try:
        # __file__ → ai/ → init/ → base/ → support/ → classes/ → usekit/
        current = Path(__file__).resolve()
        package_root = current.parent.parent.parent.parent.parent.parent
        candidate = package_root / "sys" / "sys_yaml" / "sys_ai.yaml"
        if candidate.exists():
            return candidate
    except Exception:
        pass

    try:
        from usekit.classes.common.utils.helper_const import get_base_path
        return get_base_path() / "usekit/sys/sys_yaml/sys_ai.yaml"
    except Exception:
        return Path("usekit/sys/sys_yaml/sys_ai.yaml")


# ── Load + cache ────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load() -> Dict[str, Any]:
    """Load sys_ai.yaml once. Empty/missing returns a safe default."""
    p = _yaml_path()
    if not p.exists():
        return {
            "default_provider": None,
            "tiers": {},
            "providers": {},
        }
    try:
        import yaml
        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # Defensive defaults so callers don't have to check
        data.setdefault("default_provider", None)
        data.setdefault("tiers", {})
        data.setdefault("providers", {})
        return data
    except Exception as e:
        # Don't crash the editor on a typo in yaml — log and return empty.
        print(f"[sbi_ai_meta] failed to load {p}: {e}")
        return {"default_provider": None, "tiers": {}, "providers": {}}


def clear_cache() -> None:
    """Drop the cached yaml. Call after editing sys_ai.yaml."""
    _load.cache_clear()


# ── Public accessors ────────────────────────────────────────────────

def all_meta() -> Dict[str, Any]:
    """Full registry. Used by the /api/ai_meta endpoint."""
    return _load()


def yaml_path() -> str:
    """Absolute path to sys_ai.yaml (for debugging / display)."""
    return str(_yaml_path())


def tiers() -> Dict[str, Dict[str, Any]]:
    return _load().get("tiers", {})


def providers() -> Dict[str, Dict[str, Any]]:
    return _load().get("providers", {})


def provider_of(alias: str) -> Optional[str]:
    """
    Which provider owns this model alias?
    'G20F' → 'gemini', 'GPT4O' → 'openai', etc.
    Case-insensitive on alias.
    """
    if not alias:
        return None
    key = alias.upper()
    for name, pdata in providers().items():
        if key in (pdata.get("models") or {}):
            return name
    return None


def resolve_model(alias_or_name: str, provider: Optional[str] = None) -> str:
    """
    'G20F' → 'gemini-2.0-flash'. Pass-through if already a full name
    or if alias is unknown.

    If `provider` given, only that provider's model table is consulted
    (avoids cross-provider alias collisions).
    """
    if not alias_or_name:
        return ""
    key = alias_or_name.upper()

    if provider:
        pdata = providers().get(provider) or {}
        models = pdata.get("models") or {}
        if key in models:
            return models[key]
        return alias_or_name

    # Search all providers
    for pdata in providers().values():
        models = pdata.get("models") or {}
        if key in models:
            return models[key]
    return alias_or_name


def adapter_of(provider: str) -> str:
    """ua adapter name for this provider. Empty string for CLI/unknown."""
    pdata = providers().get(provider) or {}
    return pdata.get("adapter", "") or ""


def default_provider() -> str:
    """Global first-boot provider. Falls back to 'qwen' if yaml missing."""
    return _load().get("default_provider") or "qwen"


def default_model(provider: str) -> str:
    """That provider's default model alias. Empty string if not set."""
    pdata = providers().get(provider) or {}
    return pdata.get("default", "") or ""


def enabled_providers() -> List[str]:
    """Names of providers with enabled: true (or unset)."""
    return [n for n, p in providers().items() if p.get("enabled", True)]


def is_cli(provider: str) -> bool:
    """True if provider's tier is 'cli' (subprocess dispatch)."""
    pdata = providers().get(provider) or {}
    return pdata.get("tier") == "cli"


__all__ = [
    "all_meta",
    "yaml_path",
    "tiers",
    "providers",
    "provider_of",
    "resolve_model",
    "adapter_of",
    "default_provider",
    "default_model",
    "enabled_providers",
    "is_cli",
    "clear_cache",
]

# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
