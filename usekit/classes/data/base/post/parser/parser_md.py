# Path: usekit.classes.data.base.post.parser.parser_md.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Markdown parser - reuses TXT parser (Markdown is text!)
# Philosophy: MD = TXT with markdown syntax. No need for separate implementation.
# -----------------------------------------------------------------------------------------------

# Markdown files are plain text files with markdown syntax
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
Markdown Parser - Complete TXT Feature Set

All TXT parser features work with .md files:

Basic Usage:
    content = load("README.md")
    lines = load("notes.md", lines=True)
    dump("# Title\n\nContent", "doc.md")

Search (grep-like):
    errors = load("log.md", keydata="ERROR")
    todos = load("tasks.md", keydata="^- \\[ \\]", regex=True)
    headers = load("doc.md", keydata="^#", regex=True)

Tail Operations:
    top10 = load("changelog.md", tail_top=10)
    recent = load("notes.md", tail_bottom=20)

Replace Operations:
    # Not recommended for markdown (structure-sensitive)
    # But available if needed

Append:
    dump("## New Section", "doc.md", append=True)
    dump("- New item", "list.md", append=True)

All parameters from TXT parser are supported:
    - keydata, regex, case_sensitive, invert_match
    - tail_all, tail_top, tail_mid, tail_bottom
    - line_numbers, strip, strip_empty
    - append, append_newline, replace_all
    - keydata_exists (performance optimization)
"""


# ===============================================================================
# Markdown-Specific Helpers (Future Extension)
# ===============================================================================
"""
Future enhancements for markdown-specific features:

- Front matter parsing (YAML/TOML)
- Heading extraction
- Link extraction
- Code block extraction
- Table parsing
- Metadata handling

These would be added to parser_md_sub.py when needed,
while still leveraging TXT parser for basic I/O.
"""


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
