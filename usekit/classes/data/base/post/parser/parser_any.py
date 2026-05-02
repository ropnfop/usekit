# Path: usekit.classes.data.base.post.parser.parser_any.py
# -----------------------------------------------------------------------------------------------
#  Parser ANY - Delegates to TXT Parser
#  Created by: THE Little Prince × ROP × FOP'
# -----------------------------------------------------------------------------------------------
"""
'any' format is a special case:
- Not a real parser
- Simply delegates to parser_txt
- Treats all files as text
"""

from usekit.classes.data.base.post.parser.parser_txt import (
    load,
    dump,
    loads,
    dumps,
)


# Re-export all TXT parser functions
__all__ = [
    "load",
    "dump", 
    "loads",
    "dumps",
]


# Note: parser_any.py is just a thin wrapper
# All actual parsing is done by parser_txt.py
