# Path: usekit.classes.data.base.post.parser.parser_km.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: KeyMemory (.km) parser - reuses TXT parser
# Philosophy: KM = TXT with anchor syntax. Leverage existing infrastructure.
# -----------------------------------------------------------------------------------------------

# KeyMemory files are plain text files with anchor syntax (@ANCHOR = /path)
# Therefore, we simply reuse the TXT parser which already has:
# - load/loads/dump/dumps with all features
# - keydata search (grep-like)
# - tail operations (head/tail/mid)
# - replace operations (sed-like)
# - append modes, safe writes, atomic operations

from usekit.classes.data.base.post.parser.parser_txt import (
    load,
    loads,
    dump,
    dumps,
)

# Re-export for API consistency
__all__ = [
    "load",
    "loads", 
    "dump",
    "dumps",
]


# ===============================================================================
# Usage Examples
# ===============================================================================
"""
KeyMemory Parser - Complete TXT Feature Set

All TXT parser features work with .km files:

Basic Usage:
    content = load("paths.km")
    lines = load("paths.km", lines=True)
    dump("@BASE = /project", "paths.km")

Search (grep-like):
    # Find all anchors starting with @MODEL
    models = load("paths.km", keydata="^@MODEL", regex=True)
    
    # Find all anchors using @BASE
    refs = load("paths.km", keydata="@BASE")
    
    # Find comments
    comments = load("paths.km", keydata="^#", regex=True)

Tail Operations:
    # View first 10 anchors
    top10 = load("paths.km", tail_top=10)
    
    # View last 5 anchors
    recent = load("paths.km", tail_bottom=5)

Replace Operations:
    # Update anchor path
    count = dump("/new/path", "paths.km", 
                 keydata="^@BASE = ", 
                 regex=True)
    
    # Replace all references to old path
    count = dump("/new/base", "paths.km",
                 keydata="/old/base",
                 replace_all=True)

Append:
    # Add new anchor
    dump("@NEW = /new/path", "paths.km", append=True)
    
    # Add with comment
    dump("# New section", "paths.km", append=True)
    dump("@SECTION = /path", "paths.km", append=True)

All parameters from TXT parser are supported:
    - keydata, regex, case_sensitive, invert_match
    - tail_all, tail_top, tail_mid, tail_bottom
    - line_numbers, strip, strip_empty
    - append, append_newline, replace_all
    - keydata_exists (performance optimization)

For advanced anchor parsing and resolution, see:
    - parser_km_sub.py (parsing helpers)
    - usekit.tools.keymemory (KeyMemory class)
"""


# ===============================================================================
# KM-Specific Helpers (Future Extension)
# ===============================================================================
"""
Future enhancements for KM-specific features:

- Anchor parsing (@ANCHOR = /path)
- Anchor resolution (@CHILD = @PARENT/sub)
- Format validation (@ prefix, = binding)
- Anchor dependency graph
- Circular reference detection
- Anchor usage tracking
- Auto-formatting

These would be added to parser_km_sub.py when needed,
while still leveraging TXT parser for basic I/O.
"""


# ===============================================================================
# Integration Points
# ===============================================================================
"""
Integration with USEKIT:

1. IO Level (u.rkb / u.wkb):
   content = u.rkb("paths")           # Read as text
   u.wkb(content, "paths")            # Write as text
   
2. Tool Level (KeyMemory):
   from usekit.tools.keymemory import KeyMemory
   km = KeyMemory.load("paths.km")   # Parse + resolve anchors
   path = km.resolve("@BASE")         # Get resolved path
   
3. System Level (sys_path.km):
   # Automatically loaded by KeyMemory for preset resolution
   # Users don't directly interact with sys_path.km
   path = km.resolve("@blue/test")    # Uses sys_path.km internally
"""


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
