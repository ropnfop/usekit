"""
KM Quick Start Example
======================

KM is a routing language for USEKIT.
It maps short symbolic names to files, modules, and functions.

Symbols:
    @   reference / anchor / alias
    $   leaf target splitter
    .   sub-path / route segment
    :   function selector
    =   alias binding
    |   peer set separator
    []  group wrapper
    #   comment

Run this file top-to-bottom. Each section is independent.
"""

from usekit import u, uk, uw


# ============================================================
# 1. Create KM files with uk
# ============================================================

# JSON route aliases
jb_km = """# _jb.km — json/base aliases
@card    = @JB.srs$cards
@session = @JB.ai$session
@config  = @JB.ai$config
@ai_data = [@session | @config]
"""
uk.write(jb_km, "json", "base")

# Python route aliases
pb_km = """# _pb.km — pyp/base aliases
@calc = @PB$calc
@demo = @PB$demo

# Function kit — cherry-pick functions from multiple modules
@my_kit = ("@calc: add, multiply", "@demo: report")
"""
uk.write(pb_km, "pyp", "base")

uw.ok("[1] KM files created")


# ============================================================
# 2. Data I/O via @ alias
# ============================================================

# Write — $ alias resolves to directory + file
u.wjb({"q": "1+1", "a": "2", "tags": ["math"]}, "@card.math_001")
u.wjb({"provider": "groq", "started": "2026-05-25"}, "@session.today")
u.wjb({"model": "llama-3.3-70b", "temperature": 0.3}, "@config.groq")

# Read
uw.p(u.rjb("@card.math_001"))
uw.p(u.rjb("@session.today"))
uw.p(u.rjb("@config.groq"))

# Check
uw.p(u.hjb("@card.math_001"))      # True
uw.p(u.hjb("@card.missing_999"))   # False

uw.ok("[2] Data I/O via alias")


# ============================================================
# 3. Group alias — read wide, write precise
# ============================================================

# Group searches all member directories
uw.p(u.rjb("@ai_data.today"))   # finds in session/
uw.p(u.rjb("@ai_data.groq"))    # finds in config/
uw.p(u.hjb("@ai_data.today"))   # True

# Group write is blocked — ambiguous target
try:
    u.wjb({"test": 1}, "@ai_data.new_file")
except ValueError as e:
    uw.warn(f"Blocked: {e}")

uw.ok("[3] Group alias")


# ============================================================
# 4. Module import via $ alias
# ============================================================

# $ leaf tells KM which file to import
mod = u.ipb("@calc")
uw.p(mod.add(3, 5))         # 8
uw.p(mod.multiply(4, 7))    # 28

mo = u.ipb("@demo")
uw.p(mo.report("Alice", "95"))

uw.ok("[4] Module import")


# ============================================================
# 5. : function selector — cherry-pick from module
# ============================================================

# Single function
add = u.ipb("@calc:add")
uw.p(add(10, 20))           # 30

# Multiple functions
funcs = u.ipb("@calc:add,multiply")
uw.p(funcs["add"](3, 5))        # 8
uw.p(funcs["multiply"](4, 7))   # 28

# Execute directly
uw.p(u.xpb("@calc:add", 100, 200))        # 300
uw.p(u.xpb("@demo:report", "Bob", "88"))

uw.ok("[5] Function selector")


# ============================================================
# 6. uk.support() — function kit loader
# ============================================================

# Load entire function kit from km definition
kit = uk.support("my_kit")
uw.p(kit)                           # <Kit @my_kit: add, multiply, report>

uw.p(kit.add(3, 5))                 # 8
uw.p(kit.multiply(4, 7))            # 28
uw.p(kit.report("Charlie", "92"))

uw.ok("[6] Function kit")


# ============================================================
# 7. uk management — inspect, add, remove
# ============================================================

# Info
uk.info("json", "base")

# List (raw)
uw.p(uk.list("json", "base"))

# List (resolved paths)
uw.p(uk.list("json", "base", resolve=True))

# Add alias
uk.add("user", "@JB.users$profile", "json", "base")
uw.p("@user" in uk.list("json", "base"))   # True

# Remove alias
uk.remove("user", "json", "base")
uw.p("@user" in uk.list("json", "base"))   # False

# System anchors
uw.p(uk.anchors())

uw.ok("[7] UK management")


# ============================================================
# 8. Without KM — direct path (KM is optional)
# ============================================================

# Everything works without aliases too
mod = u.ipb("calc")
uw.p(mod.add(3, 5))                    # 8
uw.p(u.xpb("calc:add", 100, 200))      # 300

uw.ok("[8] Direct path (no KM)")


# ============================================================
# 9. Level 2 — Transform Pipeline
# ============================================================

# Flatten nested dict to leaf table
config = u.rjb("@config.groq")
leaf = uk.flatten(config)
uw.p(leaf)
# [{"path": "", "key": "model", "value": "llama-3.3-70b"},
#  {"path": "", "key": "temperature", "value": 0.3}]

# Query: change model
updated = uk.query(leaf, "UPDATE SET value = 'gpt-4' WHERE key = 'model'")
uw.p(uk.reconstruct(updated))
# {"model": "gpt-4", "temperature": 0.3}

# Pipeline shorthand: flatten → query chain → reconstruct
original = {
    "ai": {"config": {"model": "qwen", "temperature": 0.3}},
    "srs": {"cards": {"math_001": {"q": "1+1", "a": "2"}}}
}

# Keep only ai/* and update model
result = uk.pipe(original, [
    "SELECT * WHERE path LIKE 'ai/%'",
    "UPDATE SET value = 'gpt-4' WHERE key = 'model'",
])
uw.p(result)
# {"ai": {"config": {"model": "gpt-4", "temperature": 0.3}}}

# Insert new field
result2 = uk.pipe(original, [
    "INSERT path='ai/config' key='max_tokens' value=1000",
])
uw.p(result2["ai"]["config"]["max_tokens"])  # 1000

# Delete by path pattern
result3 = uk.pipe(original, [
    "DELETE WHERE path LIKE 'srs/%'",
])
uw.p("srs" not in result3)  # True

uw.ok("[9] Level 2 Transform Pipeline")


# ============================================================
# Summary
# ============================================================

print()
print("=" * 50)
print("KM Quick Start — All sections complete!")
print()
print("  @   reference     @JB, @card")
print("  $   target split  @PB$calc")
print("  .   sub-path      @card.math_001")
print("  :   function      @calc:add")
print("  =   alias bind    @calc = @PB$calc")
print("  |   peer set      [@session | @config]")
print("  #   comment")
print()
print("  Level 1 — Routing")
print("  uk.write()       create km file")
print("  uk.read()        read km file")
print("  uk.list()        list aliases")
print("  uk.add()         add alias")
print("  uk.remove()      remove alias")
print("  uk.info()        inspect aliases")
print("  uk.support()     load function kit")
print("  uk.clear()       clear cache")
print()
print("  Level 2 — Transform")
print("  uk.flatten()     JSON → leaf table")
print("  uk.reconstruct() leaf table → JSON")
print("  uk.query()       KQL on leaf table")
print("  uk.pipe()        flatten → query → reconstruct")
print()
print("KM in 4 lines:")
print('  u.wjb(data, "@card.math_001")')
print('  add = u.ipb("@calc:add")')
print('  kit = uk.support("my_kit")')
print('  result = uk.pipe(data, ["SELECT * WHERE ..."])')
print("=" * 50)
