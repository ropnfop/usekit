# Path: usekit/regex/ur_proxy.py
# --------------------------------------------------------------
#  URProxy : entrypoint exposing both chain-style and single-run
# --------------------------------------------------------------

import re
from .ur_chain import UR


class URProxy:

    # -------------------------------
    # Chain entry
    # -------------------------------
    def re(self, text):
        """Start chain mode"""
        return UR(text)

    # -------------------------------
    # Single-run utilities
    # -------------------------------

    def sub(self, pat, repl, text):
        return re.sub(pat, repl, text)

    def rm(self, pat, text):
        return re.sub(pat, "", text)

    def rep(self, old, new, text):
        return text.replace(old, new)

    def grep(self, pat, text):
        return re.findall(pat, text)

    def cut(self, pat, text):
        return re.split(pat, text)