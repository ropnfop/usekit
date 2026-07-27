# Path: usekit.llm.provider.__init__.py
# -----------------------------------------------------------------------
#  Provider adapter base interface
# -----------------------------------------------------------------------


class ProviderBase:
    """All provider adapters implement this interface."""

    name: str = "base"

    def connect(self, config: dict) -> dict:
        """Connect to provider. Returns session info dict."""
        raise NotImplementedError

    def send(self, prompt: str, config: dict) -> any:
        """Send prompt. Returns raw response."""
        raise NotImplementedError

    def ping(self, config: dict) -> dict:
        """Health check → {ok: bool, elapsed: float}"""
        raise NotImplementedError

    def close(self) -> None:
        """Close session."""
        pass
