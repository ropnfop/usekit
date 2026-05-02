# Path: usekit.help.index.topic.help_part1_en.py
# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Memory-Oriented Software Architecture Documentation
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from typing import Optional, Literal
import textwrap


# ===============================================================================
# Help Topics
# ===============================================================================

HELP_TOPICS = {
    "overview": "MOSA overview",
    "alias": "Alias mapping system",
    "action": "Action list (read, write, ...)",
    "object": "Format list (json, yaml, ...)",
    "location": "Location list (base, sub, ...)",
    "pattern": "Pattern matching usage",
    "walk": "Recursive search (walk)",
    "keydata": "Nested path traversal (keydata)",
    "examples": "Usage examples",
    "quick": "Quick start guide",
}


# ===============================================================================
# Help Content - Overview
# ===============================================================================

HELP_OVERVIEW = """
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║  MOSA - Memory-Oriented Software Architecture                           ║
║  Software architecture that mirrors human memory structure               ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 Core Structure
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    USE.[ACTION].[OBJECT].[LOCATION]
    
    Example: u.rjb()  →  use.read.json.base()

📚 Key Concepts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • ACTION   : What to do (read, write, update, delete, has, ...)
    • OBJECT   : Which format (json, yaml, txt, csv, ...)
    • LOCATION : Where to do it (base, sub, now, tmp, ...)

🏗️ 3-Layer Architecture
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    DATA  : r w u d h e   read/write/update/delete/has/emit
    NAVI  : p f l g s     path/find/list/get/set
    EXEC  : x i b c       exec/import/boot/close

🔍 Help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.help()              # Full overview
    u.help("alias")       # Alias mapping
    u.help("action")      # Action list
    u.help("object")      # Format list
    u.help("location")    # Location list
    u.help("examples")    # Usage examples
    u.help("quick")       # Quick start

💡 Philosophy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "Code is not function, it is memory"
    "Users don't memorize functions — functions follow the user's memory"
"""


# ===============================================================================
# Help Content - Alias
# ===============================================================================

HELP_ALIAS = """
╔══════════════════════════════════════════════════════════════════════════╗
║  Alias Mapping                                                           ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 Alias Principles
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. First-letter based — no collisions
    2. 3 letters = action + format + location
    3. 16 actions × 10 formats × 8 locations

📊 ACTION (16)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    DATA (6):
    • r - read       u.rjb()   Read file
    • w - write      u.wjb()   Write file
    • u - update     u.ujb()   Update file
    • d - delete     u.djb()   Delete file
    • h - has        u.hjb()   Check existence
    • e - emit       u.ejm()   Memory serialization (mem only)
    
    NAVI (5):
    • p - path       u.pjb()   Get path
    • f - find       u.fjb()   Search
    • l - list       u.ljb()   List directory
    • g - get        u.gjb()   Get value
    • s - set        u.sjb()   Set value
    
    EXEC (4):
    • x - exec       u.xpb()   Execute
    • i - imp        u.ipb()   Import module
    • b - boot       u.bpb()   Boot module
    • c - close      u.cpb()   Close/cleanup

📦 OBJECT (10 formats)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    General:
    • j - json       u.rjb()   ⭐⭐⭐ Primary
    • y - yaml       u.ryb()   ⭐⭐⭐
    • t - txt        u.rtb()   ⭐⭐⭐
    • c - csv        u.rcb()   ⭐⭐
    • m - md         u.rmb()   ⭐⭐
    
    Specialized:
    • s - sql        u.rsb()   SQL query
    • d - ddl        u.rdb()   DDL script
    • p - pyp        u.rpb()   Python file
    • k - km         u.rkb()   Keymap
    • a - any        u.rab()   Any format

📍 LOCATION (8)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • b - base       u.rjb()   Base directory
    • s - sub        u.rjs()   Sub directory
    • d - dir        u.rjd()   User-specified
    • n - now        u.rjn()   Current directory
    • t - tmp        u.rjt()   Temporary
    • p - pre        u.rjp()   Preset
    • c - cache      u.rjc()   Cache
    • m - mem        u.rjm()   Memory (emit only)

🎨 Combination Examples
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.rjb()         # read json base
    u.rjs()         # read json sub
    u.wyt()         # write yaml tmp
    u.hjb()         # has json base (check existence)
    u.ejm()         # emit json mem (memory serialization)
    u.xpb()         # exec pyp base (run Python)

💡 Mnemonic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.[r/w/u/d/h/e][j/y/c/t/m/s/d/p/k/a][b/s/d/n/t/p/c/m]
       ↑            ↑                     ↑
     action(16)   format(10)           location(8)
"""


# ===============================================================================
# Help Content - Action
# ===============================================================================

HELP_ACTION = """
╔══════════════════════════════════════════════════════════════════════════╗
║  Actions                                                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

📖 DATA (6) — File I/O
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    read (r)
        Read file
        e.g.: u.rjb()  u.rjb(name="config")
        
    write (w)
        Write file
        e.g.: u.wjb(data={"key": "value"})
        
    update (u)
        Update file (merge with existing data)
        e.g.: u.ujb(data={"new": "data"})
        
    delete (d)
        Delete file
        e.g.: u.djb(name="old_file")
        
    has (h)
        Check file existence (True/False)
        e.g.: u.hjb(name="config")
        
    emit (e)
        Memory serialization (no file I/O)
        e.g.: u.ejm(data={"key": "value"})
        ⚠️ mem location only

🔍 NAVI (5) — Navigation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    path (p)
        Return file path
        e.g.: u.pjb(name="config")  # Path object
        
    find (f)
        Pattern search
        e.g.: u.fjb(name="user_*")
        
    list (l)
        List directory
        e.g.: u.ljb()  # All json files
        
    get (g)
        Get value (read + keydata)
        e.g.: u.gjb(name="config", keydata="user/email")
        
    set (s)
        Set value (update + keydata)
        e.g.: u.sjb(name="config", keydata="user/name", data="Alice")

⚙️ EXEC (4) — Execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    exec (x)
        Execute code
        e.g.: u.xpb("module:func", arg1, arg2)
        
    imp (i)
        Dynamic module import
        e.g.: u.ipb("module_name")
        
    boot (b)
        Boot module (initialize + execute)
        e.g.: u.bpb("module_name")
        
    close (c)
        Close / cleanup
        e.g.: u.cpb()
"""

# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "HELP_TOPICS",
    "HELP_OVERVIEW",
    "HELP_ALIAS",
    "HELP_ACTION",
]
