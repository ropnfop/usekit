# Path: usekit.llm.base.init.lli_key.py
# -----------------------------------------------------------------------
#  API key management
# -----------------------------------------------------------------------


class KeyStore:
    """Simple API key holder with masking."""

    def __init__(self):
        self._keys = {}  # provider → key

    def set(self, key: str, provider: str = "_default"):
        """Store API key for provider."""
        self._keys[provider] = key

    def get(self, provider: str = "_default") -> str:
        """Get raw key."""
        return self._keys.get(provider, self._keys.get("_default", ""))

    def masked(self, provider: str = "_default") -> str:
        """Get masked key for display."""
        k = self.get(provider)
        if not k:
            return "(none)"
        if len(k) <= 8:
            return "****"
        return f"{k[:4]}...{k[-4:]}"

    def has(self, provider: str = "_default") -> bool:
        return bool(self.get(provider))

    def clear(self, provider: str = None):
        if provider:
            self._keys.pop(provider, None)
        else:
            self._keys.clear()
