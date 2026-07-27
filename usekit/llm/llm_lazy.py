# Path: usekit.llm.llm_lazy.py
# -----------------------------------------------------------------------
#  Lazy wrapper for AIHandler (ua)
#  Matches _LazyDB / _LazyTime pattern in use_support.py
# -----------------------------------------------------------------------

from usekit.classes.common.init.helper_lazy import lazy


class _LazyAI:
    """
    Lazy wrapper for AIHandler — delays import until first access.

    Same pattern as _LazyDB for ud.
    """

    def __init__(self):
        self._ai_lazy = lazy.value(self._create_ai)

    def _create_ai(self):
        from usekit.llm.handler.ua_handler import ua
        return ua

    def __getattr__(self, name):
        return getattr(self._ai_lazy(), name)

    def __call__(self, *args, **kwargs):
        return self._ai_lazy()(*args, **kwargs)

    def __repr__(self):
        if self._ai_lazy.is_computed:
            inner = self._ai_lazy()
            return repr(inner)
        elif self._ai_lazy.is_loading:
            return "<LazyAI [loading...]>"
        else:
            return "<LazyAI [not loaded]>"

    def preload(self):
        self._ai_lazy.start_background_load()
        return self

    @property
    def is_loaded(self):
        return self._ai_lazy.is_computed

    @property
    def is_loading(self):
        return self._ai_lazy.is_loading


ua = _LazyAI()

__all__ = ["_LazyAI", "ua"]
