"""
us.api — Contract Engine Tests
Run in usekit editor to verify us.api is working.
"""

from usekit import us, uw


# ============================================================
# Test A-1: us.api exists
# ============================================================
uw.p(us.api)
uw.ok("A-1: us.api exists")


# ============================================================
# Test A-2: validate contract
# ============================================================
errors = us.api.validate("contract/api")
if errors:
    for e in errors:
        uw.warn(e)
else:
    uw.ok("A-2: contract valid (0 errors)")


# ============================================================
# Test A-3: info
# ============================================================
us.api.info("contract/api")
uw.ok("A-3: info printed")


# ============================================================
# Test A-4: routes list
# ============================================================
routes = us.api.routes("contract/api")
uw.p(f"Total routes: {len(routes)}")
for r in routes:
    uw.p(f"  [{r['type']:6}] {r['method']:4} {r['path']}")
uw.ok("A-4: routes listed")


# ============================================================
# Summary
# ============================================================
print()
print("=" * 50)
print("us.api — Contract Engine Tests Complete!")
print("=" * 50)
