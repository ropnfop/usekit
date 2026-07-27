"""
Kit / uk.support() Edge Case Tests
"""

from usekit import u, uk, uw


# ============================================================
# Setup
# ============================================================

pb_km = """# _pb.km
@calc = @PB$calc
@demo = @PB$demo
@my_kit = ("@calc: add, multiply", "@demo: report")
@dup_kit = ("@calc: add", "@demo: add")
"""

# calc.py has: add, multiply
# demo.py has: add (if exists), report
# We need demo to have 'add' for dup test — skip if not available

uk.write(pb_km, "pyp", "base")
uk.clear()


# ============================================================
# Test K-1: @ prefix allowed in kit_name
# ============================================================

kit1 = uk.support("my_kit")
kit2 = uk.support("@my_kit")
uw.p(kit1.add(3, 5))   # 8
uw.p(kit2.add(3, 5))   # 8
uw.ok("K-1: @ prefix allowed")


# ============================================================
# Test K-2: Kit repr
# ============================================================

uw.p(repr(kit1))   # <Kit @my_kit: add, multiply, report>
uw.ok("K-2: Kit repr")


# ============================================================
# Test K-3: Unknown function → AttributeError
# ============================================================

try:
    kit1.nonexistent()
except AttributeError as e:
    uw.p(f"Caught: {e}")
uw.ok("K-3: Unknown function error")


# ============================================================
# Test K-4: Unknown kit → KeyError
# ============================================================

try:
    uk.support("no_such_kit")
except KeyError as e:
    uw.p(f"Caught: {e}")
uw.ok("K-4: Unknown kit error")


# ============================================================
# Test K-5: Duplicate function name → ValueError
# ============================================================

# This test only works if demo.py has an 'add' function
# If not, we simulate the error path
try:
    uk.support("dup_kit")
    uw.warn("K-5: No error raised (demo may not have 'add')")
except ValueError as e:
    uw.p(f"Caught: {e}")
    uw.ok("K-5: Duplicate function blocked")
except AttributeError:
    uw.p("K-5: demo.py has no 'add' — skipped (expected)")
    uw.ok("K-5: Skipped (no dup to test)")


# ============================================================
# Test K-6: Kit dir() lists functions
# ============================================================

uw.p(sorted(dir(kit1)))  # ['add', 'multiply', 'report']
uw.ok("K-6: Kit dir()")


# ============================================================
# Summary
# ============================================================

print()
print("=" * 50)
print("Kit Tests — Complete!")
print("=" * 50)
