# Path: usekit/classes/core/env/
# File: class_env.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- #

from usekit.classes.core.env.loader_env import get_env

class EnvHandler:
    def __init__(self):
        self._env = get_env()

    def get(self, key: str, default=None):
        return self._env.get(key, default)

    def keys(self):
        return list(self._env.keys())