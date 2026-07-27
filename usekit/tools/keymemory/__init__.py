# Path: usekit.tools.keymemory.__init__.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# -----------------------------------------------------------------------------------------------

"""
KeyMemory Package

.km (Key Memory) format parser and resolver

Standalone usage:
    from usekit.tools.keymemory import KeyMemory
    km = KeyMemory.load("paths.km")
    path = km.resolve("@MODEL_CLS")

USEKIT-integrated usage:
    from usekit.tools.keymemory import KeyMemory
    km = KeyMemory.load_route("json", "base")
    path = km.resolve("@card")

Architecture:
    KMParser (thin wrapper) → parser_km_sub (parsing engine)
    KeyMemory.load_route() → helper_km_system (system anchor injection)
"""

from .base import KeyMemory
from .parser import KMParser

__version__ = "0.2.0"
__all__ = ['KeyMemory', 'KMParser']
