# Path: usekit.llm.base.init.lli_config.py
# -----------------------------------------------------------------------
#  Generation config management
# -----------------------------------------------------------------------

# Default generation params
_DEFAULTS = {
    "temperature": 0.3,
    "max_tokens": 1200,
}


class LLMConfig:
    """Mutable config store for generation params."""

    def __init__(self):
        self._data = dict(_DEFAULTS)

    def set(self, **kw):
        """Set one or more config values."""
        self._data.update(kw)

    def get(self, key: str, default=None):
        """Get a config value."""
        return self._data.get(key, default)

    def merge(self, overrides: dict = None) -> dict:
        """Return merged config (base + overrides)."""
        if not overrides:
            return dict(self._data)
        merged = dict(self._data)
        merged.update(overrides)
        return merged

    def reset(self):
        """Reset to defaults."""
        self._data = dict(_DEFAULTS)

    def to_dict(self) -> dict:
        return dict(self._data)

    def __repr__(self):
        return f"<LLMConfig {self._data}>"
