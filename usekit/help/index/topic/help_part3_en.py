# Path: usekit.help.index.topic.help_part3_en.py
# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Examples, Quick Start (English)
# -----------------------------------------------------------------------------------------------

HELP_EXAMPLES = """
╔══════════════════════════════════════════════════════════════════════════╗
║  Usage Examples                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 Basic Usage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Read
    data = u.rjb()                    # Read config.json (default)
    data = u.rjb(name="users")        # Read users.json
    
    # Write
    u.wjb(data={"key": "value"})      # Write to dumps
    u.wjb(data={"key": "value"}, name="new_file")
    
    # Update
    u.ujb(data={"new": "data"})       # Merge
    
    # Delete
    u.djb(name="old_file")            # Delete file
    
    # Check existence
    if u.hjb(name="config"):
        print("File exists")

📍 Location
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Sub directory
    u.rjs(name="config")             # data/json/json_sub/config.json
    
    # Current directory
    u.rjn(name="local")              # Current working dir
    
    # Temp directory
    u.wjt(data={"temp": "data"})     # tmp/config.json

🎨 Pattern Matching
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Read all user files
    users = u.rjb(name="user_*")
    for user in users:
        print(user["file"], user["data"])
    
    # Search with pattern
    logs = u.rjb(name="log_2024*", walk=True)
    
    # Delete temp files
    result = u.djt(name="temp_*")
    print(f"Deleted: {result['success']} files")

🔍 keydata Usage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Read nested path
    email = u.rjb(name="config", keydata="user/email")
    
    # Update nested path
    u.ujb(name="config", keydata="user/name", data="Bob")
    
    # Array access
    first_item = u.rjb(keydata="items[0]/name")
    
    # Specific field from multiple files
    emails = u.rjb(name="user_*", keydata="email")

🔄 Recursive Search
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Search all subdirectories
    configs = u.rjb(name="config_*", walk=True)
    
    # Recursive search from specific directory
    u.rjs(name="settings_*", walk=True)

🎭 Real-World Examples
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. User data management
    # Add new user
    u.wjb(name="user_alice", data={
        "name": "Alice",
        "email": "alice@example.com",
        "created": "2024-11-07"
    })
    
    # Update email only
    u.ujb(name="user_alice", keydata="email", data="newemail@example.com")
    
    # Query all user emails
    emails = u.rjb(name="user_*", keydata="email")
    
    # 2. Config management
    # Read default config
    config = u.rjb(name="config")
    
    # Update specific setting
    u.ujb(keydata="database/host", data="localhost")
    
    # 3. Temp data cleanup
    # Delete old temp files
    result = u.djt(name="cache_*")
    print(f"{result['success']} files deleted")
    
    # 4. Log analysis
    # Find recent log files
    logs = u.rjb(name="log_20241107_*", walk=True)
    for log in logs:
        print(log["path"])

💎 Advanced Patterns
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Conditional update
    if u.hjb(name="config"):
        u.ujb(data={"updated": "2024-11-07"})
    else:
        u.wjb(data={"created": "2024-11-07"})
    
    # Batch processing
    for user_file in u.ljb():
        data = u.rjb(name=user_file)
        # Processing logic
        u.ujb(name=user_file, data=processed_data)
    
    # Create backup
    data = u.rjb(name="important")
    u.wjt(name=f"backup_{datetime.now():%Y%m%d}", data=data)
"""

HELP_QUICK = """
╔══════════════════════════════════════════════════════════════════════════╗
║  Quick Start Guide                                                       ║
╚══════════════════════════════════════════════════════════════════════════╝

⚡ Start in 5 Minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ Basics (JSON) — small → big → option
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Write
    u.wjb(data={"name": "Alice", "age": 25})
    
    # Read
    data = u.rjb()
    print(data["name"])  # Alice
    
    # Update
    u.ujb(data={"age": 26})
    
    # Delete
    u.djb()

2️⃣ Naming Files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Specify filename
    u.wjb(data={"alice": {...}}, name="users")
    u.rjb(name="users")
    
    # Extension added automatically (users.json)
    # No filename = virtual memory (dumps)

3️⃣ Change Location
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.rjb()    # base directory (default)
    u.rjs()    # sub directory (yaml-specified path)
    u.rjn()    # current directory
    u.rjd()    # user-specified directory
    u.rjt()    # temp directory (tmp/)
    u.rjc()    # cache directory

4️⃣ Multiple Files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # All files starting with user_
    users = u.rjb(name="user_*")
    for user in users:
        print(user["file"], user["data"])

5️⃣ Nested Data Access
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Data: {"user": {"profile": {"email": "a@b.com"}}}
    
    # Read email only
    email = u.rjb(keydata="user/profile/email")
    
    # Update email only
    u.ujb(keydata="user/profile/email", data="new@example.com")

📝 Other Formats
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.wyb()    # YAML
    u.wtb()    # Text
    u.wcb()    # CSV
    u.wmb()    # Markdown

🎯 3 Core Patterns
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. Basic usage
       u.rjb()  u.wjb()  u.ujb()  u.djb()
    
    2. Name + location
       u.rjs(name="config")
    
    3. Pattern + keydata
       u.rjb(name="user_*", keydata="email")

💡 Easy Mnemonic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.[what][which format][where]  →  verb object adverb
    
    u.r j b    →  use.read.json.base
      ↑ ↑ ↑
      read/write  json/yaml  base/sub
      
    Examples:
    u.rjb()    read json base
    u.wys()    write yaml sub
    u.ujt()    update json tmp

🚀 Try It Now
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Step 1: Write data
    u.wjb(data={"hello": "MOSA"})
    
    # Step 2: Read data
    print(u.rjb())
    
    # Step 3: Update
    u.ujb(data={"version": "1.0"})
    
    # Done! 🎉

📚 Learn More
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.help("examples")    # More examples
    u.help("pattern")     # Pattern matching details
    u.help("keydata")     # keydata details
"""

# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "HELP_EXAMPLES",
    "HELP_QUICK",
]
