# Path: usekit.llm.base.init.lli_conn.py
# -----------------------------------------------------------------------
#  Connection router — provider name → adapter
#
#  Now reads sys_ai.yaml via sbi_ai_meta instead of hardcoded maps.
#  _ADAPTERS = adapter-class registry (adapter name → class).
#  Everything else (base_url, model, key_env) comes from yaml.
# -----------------------------------------------------------------------

import os
from usekit.llm.provider.prov_openai import ProvOpenAI
from usekit.llm.provider.prov_gemini import ProvGemini

# Adapter class registry — adapter name → class
# sys_ai.yaml "adapter" field maps here
_ADAPTERS = {
    "openai":    ProvOpenAI,
    "gemini":    ProvGemini,
    # "anthropic": ProvAnthropic,   # TODO
}


def _meta():
    """Lazy import sbi_ai_meta to avoid circular imports."""
    from usekit.classes.support.base.init.ai.sbi_ai_meta import (
        providers, adapter_of, default_provider, default_model, resolve_model,
    )
    return providers, adapter_of, default_provider, default_model, resolve_model


def resolve_provider(name: str):
    """
    Get provider adapter instance by provider name.

    'qwen' → yaml adapter='openai' → ProvOpenAI()
    'gemini' → adapter='gemini' → ProvGemini()
    """
    key = name.lower().strip()

    _declared_adapter = ""
    try:
        providers, *_ = _meta()
        pdata = providers().get(key)
        if pdata:
            adapter_name = pdata.get("adapter", "")
            _declared_adapter = adapter_name
            if adapter_name and adapter_name in _ADAPTERS:
                return _ADAPTERS[adapter_name]()
    except Exception:
        pass

    # Fallback: try adapter name directly
    if key in _ADAPTERS:
        return _ADAPTERS[key]()

    # Provider IS declared in yaml but its adapter class is not implemented yet
    # (e.g. anthropic → ProvAnthropic is TODO). Give a precise reason instead of
    # the generic "unknown provider", so enabling it in yaml fails loudly & clearly.
    if _declared_adapter:
        raise ValueError(
            f"[lli_conn] provider '{name}' uses adapter '{_declared_adapter}' "
            f"which is not implemented yet. Implemented: {list(_ADAPTERS.keys())}"
        )

    raise ValueError(
        f"[lli_conn] unknown provider: '{name}'. "
        f"Available adapters: {list(_ADAPTERS.keys())}"
    )


def get_provider_config(provider_name: str) -> dict:
    """
    Full provider config from sys_ai.yaml.

    Returns: {base_url, model, key_env, adapter, tier, enabled, models}
    """
    key = provider_name.lower().strip()

    try:
        providers, _, _, _, resolve_model = _meta()
        pdata = providers().get(key)
    except Exception:
        return {}

    if not pdata:
        return {}

    # Resolve default model alias → full name
    default_alias = pdata.get("default", "")
    full_model = resolve_model(default_alias, key) if default_alias else ""

    # Resolve API key from env
    key_env = pdata.get("key_env") or ""
    api_key = os.getenv(key_env, "") if key_env else ""

    return {
        "base_url":   pdata.get("base_url", ""),
        "model":      full_model,
        "key_env":    key_env,
        "api_key":    api_key,
        "adapter":    pdata.get("adapter", ""),
        "tier":       pdata.get("tier", ""),
        "enabled":    pdata.get("enabled", True),
        "models":     pdata.get("models", {}),
    }


def get_default_url(provider_name: str) -> str:
    """Get default base_url from sys_ai.yaml."""
    return get_provider_config(provider_name).get("base_url", "")


def get_default_model(provider_name: str) -> str:
    """Get default model (full name) from sys_ai.yaml."""
    return get_provider_config(provider_name).get("model", "")


def get_key_env(provider_name: str) -> str:
    """Get env var name for API key."""
    return get_provider_config(provider_name).get("key_env", "")


def list_providers() -> list:
    """Available provider names from sys_ai.yaml."""
    try:
        providers, *_ = _meta()
        return list(providers().keys())
    except Exception:
        return list(_ADAPTERS.keys())
