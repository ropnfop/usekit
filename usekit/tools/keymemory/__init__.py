# Path: usekit.tools.keymemory.__init__.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# -----------------------------------------------------------------------------------------------

"""
KeyMemory Package

.km (Key Memory) format parser and resolver

Usage:
    from keymemory import KeyMemory
    
    km = KeyMemory.load("paths.km")
    path = km.resolve("@MODEL_CLS")
"""

from .base import KeyMemory
from .parser import KMParser

__version__ = "0.1.0"
__all__ = ['KeyMemory', 'KMParser']
