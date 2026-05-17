# Path: usekit.help.index.topic.help_part2_en.py
# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Memory-Oriented Software Architecture Documentation
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from typing import Optional, Literal
import textwrap

# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Pattern, Walk, Keydata (English)
# -----------------------------------------------------------------------------------------------

HELP_PATTERN = """
╔══════════════════════════════════════════════════════════════════════════╗
║  Pattern Matching                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 Pattern Characters
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    *       Match 0 or more characters
    ?       Match exactly 1 character
    %       SQL LIKE style (same as *)
    [abc]   Match one of a, b, c
    [a-z]   Match one from a to z

📖 Examples
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # All user files
    u.rjb(name="user_*")
    [user_001.json, user_002.json, user_alice.json]
    
    # Fixed length
    u.rjb(name="log_????")
    [log_2024.json, log_2025.json]
    
    # SQL LIKE style
    u.rjb(name="%test%")
    [my_test_file.json, test_config.json]
    
    # Combined
    u.rjb(name="user_[0-9]*.json")
    [user_001.json, user_123.json]

🔄 Combined with walk
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Current directory only
    u.rjb(name="user_*")
    base/user_001.json
    base/user_002.json
    
    # Including subdirectories
    u.rjb(name="user_*", walk=True)
    base/user_001.json
    base/subdir/user_002.json
    base/subdir/deep/user_003.json

📊 Return Types
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # read: list of results per file
    [
        {"file": "user_001", "path": "...", "data": {...}},
        {"file": "user_002", "path": "...", "data": {...}}
    ]
    
    # has: True if any match exists
    True / False
    
    # delete: detailed result
    {
        "deleted": [Path(...), Path(...)],
        "failed": [],
        "total": 2,
        "success": 2
    }

⚠️ Safety (delete only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Dangerous patterns blocked
    u.djb(name="*")              # ❌ ValueError
    u.djb(name="**")             # ❌ ValueError
    u.djb(name="*.*")            # ❌ ValueError
    u.djb(name="*_*", walk=True) # ❌ ValueError
    
    # Safe patterns
    u.djb(name="temp_*")         # ✅ OK
    u.djb(name="old_20241107_*") # ✅ OK
"""


HELP_WALK = """
╔══════════════════════════════════════════════════════════════════════════╗
║  Recursive Search (walk)                                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 Concept
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    walk=False (default)
        Search specified directory only
        
    walk=True
        Recursively search subdirectories

📂 Directory Structure Example
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    base/
    ├── config.json
    ├── user_001.json
    └── subdir/
        ├── user_002.json
        └── deep/
            └── user_003.json

📖 Examples
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # walk=False (default)
    u.rjb(name="user_*")
    Result: [user_001.json]  # base/ only
    
    # walk=True
    u.rjb(name="user_*", walk=True)
    Result: [
        user_001.json,         # base/
        user_002.json,         # base/subdir/
        user_003.json          # base/subdir/deep/
    ]

🔗 Relationship with loc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    loc and walk are independent!
    
    • loc: "where" to search (base/sub/now/tmp/...)
    • walk: "how deep" to search (True/False)
    
    Examples:
    u.rjs(name="config_*")              # sub/ only
    u.rjs(name="config_*", walk=True)   # sub/ and below
    u.rjt(name="temp_*", walk=True)     # tmp/ and below

⚡ Performance Note
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    walk=True searches all subdirectories,
    which can be slow with many files.
    
    • Know exact location: walk=False (default)
    • Don't know where: walk=True
    • Specific scope: combine with loc
"""


HELP_KEYDATA = """
╔══════════════════════════════════════════════════════════════════════════╗
║  Nested Path Traversal (keydata)                                         ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 Concept
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    keydata specifies a path within nested data structures.
    
    Separator: "/" (slash)
    Array: [index] or /index

📊 Data Example
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "user": {
            "name": "Alice",
            "email": "alice@example.com",
            "profile": {
                "age": 25,
                "city": "Seoul"
            }
        },
        "items": [
            {"id": 1, "name": "Item A"},
            {"id": 2, "name": "Item B"}
        ]
    }

📖 Examples
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Single key
    u.rjb(name="config", keydata="user")
    Result: {"name": "Alice", "email": "...", "profile": {...}}
    
    # Nested path
    u.rjb(name="config", keydata="user/email")
    Result: "alice@example.com"
    
    # Deeper path
    u.rjb(name="config", keydata="user/profile/city")
    Result: "Seoul"
    
    # Array index
    u.rjb(name="config", keydata="items[0]")
    u.rjb(name="config", keydata="items/0")
    Result: {"id": 1, "name": "Item A"}
    
    # Array + key
    u.rjb(name="config", keydata="items[0]/name")
    Result: "Item A"

🔧 Behavior per Action
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    read
        Return value at keydata path
        u.rjb(name="config", keydata="user/email")
        
    update
        Update only the keydata path (rest preserved)
        u.ujb(name="config", keydata="user/email", data="new@example.com")
        
    delete
        Delete only the keydata path (file preserved)
        u.djb(name="config", keydata="user/temp_data")
        
    has
        Check if keydata path exists
        u.hjb(name="config", keydata="user/email")

⚙️ Advanced Options
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    default
        Default value when keydata not found
        u.rjb(keydata="user/phone", default="N/A")
        
    recursive
        Recursively search all matching paths
        u.rjb(keydata="email", recursive=True)
        
    find_all
        Return all matching values (list)
        u.rjb(keydata="items/*/name", find_all=True)
        
    create_missing
        Auto-create intermediate paths (update/write)
        u.ujb(keydata="new/deep/path", data="value", create_missing=True)

🎨 Pattern + keydata Combined
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Read specific field from multiple files
    u.rjb(name="user_*", keydata="email")
    [
        {"file": "user_001", "data": "alice@example.com"},
        {"file": "user_002", "data": "bob@example.com"}
    ]
    
    # Delete specific field from multiple files
    u.djb(name="user_*", keydata="profile/temp_data")
    {
        "deleted": [Path(...), Path(...)],
        "success": 2
    }
"""

# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "HELP_PATTERN",
    "HELP_WALK",
    "HELP_KEYDATA",
]
