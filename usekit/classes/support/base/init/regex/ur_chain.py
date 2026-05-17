# Path: usekit/regex/ur_chain.py
# --------------------------------------------------------------
#  usekit.regex / ur : regex chain + utility
#  Author: Little Prince × ROP × FOP
# --------------------------------------------------------------

import re
from typing import Union, List


class UR:
    """Chain-based regex/string manipulation engine."""

    def __init__(self, text: Union[str, bytes]):
        self.text = text.decode() if isinstance(text, bytes) else text

    # ----------------------------------------------------------
    # Chainable regex methods
    # ----------------------------------------------------------

    def sub(self, pat, repl):
        self.text = re.sub(pat, repl, self.text)
        return self

    def rm(self, pat):
        """Remove regex pattern"""
        self.text = re.sub(pat, "", self.text)
        return self

    def rep(self, old, new):
        """Simple string replace"""
        self.text = self.text.replace(old, new)
        return self

    def grep(self, pat) -> List[str]:
        """Find all (list 반환 → 체인 종료)"""
        return re.findall(pat, self.text)

    def cut(self, pat) -> List[str]:
        """Regex split"""
        return re.split(pat, self.text)

    # ----------------------------------------------------------
    # String utilities
    # ----------------------------------------------------------

    def strip(self):
        self.text = self.text.strip()
        return self

    def upper(self):
        self.text = self.text.upper()
        return self

    def lower(self):
        self.text = self.text.lower()
        return self

    def cap(self):
        self.text = self.text.capitalize()
        return self

    def title(self):
        self.text = self.text.title()
        return self

    # ----------------------------------------------------------
    # Output
    # ----------------------------------------------------------

    def get(self):
        return self.text

    def show(self):
        print(self.text)
        return self