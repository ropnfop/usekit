# Path: usekit.llm.base.load.lll_send.py
# -----------------------------------------------------------------------
#  Unified send dispatcher
# -----------------------------------------------------------------------


def send(adapter, prompt: str, config: dict) -> dict:
    """
    Dispatch send to the active provider adapter.

    Returns raw response dict (provider-specific).
    """
    if adapter is None:
        raise RuntimeError("[lll_send] no provider connected. call ua.conn() first.")

    return adapter.send(prompt, config)
