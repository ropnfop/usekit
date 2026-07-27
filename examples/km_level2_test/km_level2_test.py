"""
KM Level 2 Transform Pipeline — Test (L2-1 ~ L2-9)
"""

from usekit import u, uk, uw


# ============================================================
# L2-1: Shallow flatten
# ============================================================
data = {"a": {"b": {"c": 1, "d": 2}}}
leaf = uk.flatten(data)
assert len(leaf) == 2, f"Expected 2, got {len(leaf)}"
assert leaf[0]["path"] == "a/b", f"Expected 'a/b', got {leaf[0]['path']!r}"
assert leaf[0]["key"] == "c", f"Expected 'c', got {leaf[0]['key']!r}"
uw.ok("L2-1: Shallow flatten")


# ============================================================
# L2-2: Deep flatten
# ============================================================
data = {"a": {"b": {"c": {"x": 1}}}}
leaf = uk.flatten(data, depth="deep")
assert leaf[0]["path"] == "a/b/c", f"Expected 'a/b/c', got {leaf[0]['path']!r}"
assert leaf[0]["key"] == "x"
uw.ok("L2-2: Deep flatten")


# ============================================================
# L2-3: Array handling
# ============================================================
data = {"items": [1, 2, 3]}
leaf = uk.flatten(data)
assert len(leaf) == 1, f"Expected 1 (array as leaf), got {len(leaf)}"
assert leaf[0]["value"] == [1, 2, 3]
uw.ok("L2-3: Array handling (scalar array = single leaf)")

# Deep: array of dicts
data2 = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
leaf2 = uk.flatten(data2)
assert len(leaf2) == 2
assert leaf2[0]["path"] == "users[0]"
assert leaf2[0]["key"] == "name"
uw.ok("L2-3b: Array of dicts")


# ============================================================
# L2-4: Round-trip
# ============================================================
original = {
    "ai": {"config": {"model": "qwen", "temperature": 0.3}},
    "srs": {"cards": {"math_001": {"q": "1+1", "a": "2"}}}
}
restored = uk.reconstruct(uk.flatten(original))
assert restored == original, f"Round-trip failed:\n  {original}\n  {restored}"
uw.ok("L2-4: Round-trip")


# ============================================================
# L2-5: SELECT query
# ============================================================
leaf = uk.flatten(original)
result = uk.query(leaf, "SELECT * WHERE path LIKE 'ai/%'")
assert len(result) == 2, f"Expected 2, got {len(result)}"
uw.ok("L2-5: SELECT query")


# ============================================================
# L2-6: UPDATE query
# ============================================================
result = uk.query(leaf, "UPDATE SET value = 'gpt-4' WHERE key = 'model'")
restored = uk.reconstruct(result)
assert restored["ai"]["config"]["model"] == "gpt-4", f"Got {restored['ai']['config']['model']!r}"
uw.ok("L2-6: UPDATE query")


# ============================================================
# L2-7: DELETE query
# ============================================================
result = uk.query(leaf, "DELETE WHERE path LIKE 'srs/%'")
restored = uk.reconstruct(result)
assert "srs" not in restored, f"srs should be deleted, got {restored.keys()}"
uw.ok("L2-7: DELETE query")


# ============================================================
# L2-8: INSERT query
# ============================================================
result = uk.query(leaf, "INSERT path='ai/config' key='max_tokens' value=1000")
restored = uk.reconstruct(result)
assert restored["ai"]["config"]["max_tokens"] == 1000
uw.ok("L2-8: INSERT query")


# ============================================================
# L2-9: Pipeline
# ============================================================
result = uk.pipe(original, [
    "SELECT * WHERE path LIKE 'ai/%'",
])
assert "srs" not in result, f"srs should be filtered out"
assert result["ai"]["config"]["model"] == "qwen"
uw.ok("L2-9: Pipeline")


# ============================================================
# Summary
# ============================================================
print()
print("=" * 50)
print("KM Level 2 — All 9 tests passed!")
print("=" * 50)
