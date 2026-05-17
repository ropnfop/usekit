#!/usr/bin/env python3
"""
JSON Append and Emit Demo for USEKIT

This example verifies JSON append behavior and memory-only JSON emit.

Tests:
1. JSONL append mode
2. Array append mode
3. Object merge mode
4. Auto append mode detection
5. u.ejm() memory JSON emit for dict/list/scalar inputs

Notes:
    u.* is used for core test operations.
    s.* is used for safe cleanup operations.

    u.ejm() means:
        emit json mem

    emit is not just a shortcut for json.dumps.
    It is USEKIT's memory serialization layer.

    It accepts common Python values such as:
        dict, list, str, int, float, bool, None, and nested structures

    Planned full semantic form:
        use.emit.json.mem()

    Current note:
        use.emit.json.mem() may not be available in the current release
        because the full-name "emit" branch is still being patched.

    Use u.ejm() for now.
"""

from usekit import u, s, ut, uw


def safe_delete_json(name):
    """
    Safely delete a JSON file.

    s.* is the safe wrapper layer.
    It is useful for cleanup or optional operations.

    Core test operations use u.* so failures remain visible.
    """
    s.djb(name)


def print_section(title):
    """Print a section header."""
    uw.p("")
    uw.p("=" * 60)
    uw.p(title)
    uw.p("=" * 60)


def test_jsonl_append():
    """Test JSONL append mode."""
    print_section("Test 1: JSONL Append Mode")

    safe_delete_json("test_daily_summary")

    u.wjb(
        {"date": ut.str(), "summary": "First entry", "user": "Alice"},
        "test_daily_summary",
        append=True,
        append_mode="jsonl",
    )

    u.wjb(
        {"date": ut.str(), "summary": "Second entry", "user": "Bob"},
        "test_daily_summary",
        append=True,
        append_mode="jsonl",
    )

    u.wjb(
        {"date": ut.str(), "summary": "Third entry", "user": "Charlie"},
        "test_daily_summary",
        append=True,
        append_mode="jsonl",
    )

    uw.p("")
    uw.p("Reading JSONL file...")

    content = u.rjb("test_daily_summary", jsonl=True)

    uw.p("")
    uw.p(f"Total entries: {len(content)}")

    for index, entry in enumerate(content, 1):
        uw.p(f"{index}. {entry['user']}: {entry['summary']}")

    assert len(content) == 3, f"Expected 3 entries, got {len(content)}"
    assert content[0]["user"] == "Alice"
    assert content[1]["user"] == "Bob"
    assert content[2]["user"] == "Charlie"

    uw.p("")
    uw.ok("JSONL append test passed")

    safe_delete_json("test_daily_summary")


def test_array_append():
    """Test array append mode."""
    print_section("Test 2: Array Append Mode")

    safe_delete_json("test_array")

    u.wjb([{"id": 1, "name": "Alice"}], "test_array")

    u.wjb(
        {"id": 2, "name": "Bob"},
        "test_array",
        append=True,
        append_mode="array",
    )

    u.wjb(
        {"id": 3, "name": "Charlie"},
        "test_array",
        append=True,
        append_mode="array",
    )

    uw.p("")
    uw.p("Reading array file...")

    content = u.rjb("test_array")

    uw.p("")
    uw.p(f"Total items: {len(content)}")

    for item in content:
        uw.p(f"  - {item['id']}: {item['name']}")

    assert len(content) == 3, f"Expected 3 items, got {len(content)}"
    assert content[0]["name"] == "Alice"
    assert content[1]["name"] == "Bob"
    assert content[2]["name"] == "Charlie"

    uw.p("")
    uw.ok("Array append test passed")

    safe_delete_json("test_array")


def test_object_append():
    """Test object merge mode."""
    print_section("Test 3: Object Merge Mode")

    safe_delete_json("test_object")

    u.wjb({"name": "Alice", "age": 30}, "test_object")

    u.wjb(
        {"city": "Seoul", "country": "Korea"},
        "test_object",
        append=True,
        append_mode="object",
    )

    u.wjb(
        {"hobby": "coding"},
        "test_object",
        append=True,
        append_mode="object",
    )

    uw.p("")
    uw.p("Reading merged object...")

    content = u.rjb("test_object")

    uw.p("")
    uw.p("Merged content:")

    for key, value in content.items():
        uw.p(f"  {key}: {value}")

    assert content["name"] == "Alice"
    assert content["age"] == 30
    assert content["city"] == "Seoul"
    assert content["country"] == "Korea"
    assert content["hobby"] == "coding"

    uw.p("")
    uw.ok("Object merge test passed")

    safe_delete_json("test_object")


def test_auto_mode():
    """Test auto append mode detection."""
    print_section("Test 4: Auto Mode Detection")

    safe_delete_json("test_auto")

    u.wjb([{"id": 1}], "test_auto")

    u.wjb(
        {"id": 2},
        "test_auto",
        append=True,
    )

    content = u.rjb("test_auto")

    assert isinstance(content, list), "Expected list"
    assert len(content) == 2, f"Expected 2 items, got {len(content)}"

    uw.p(f"Auto detected array mode: {content}")

    u.djb("test_auto")

    u.wjb({"a": 1}, "test_auto")

    u.wjb(
        {"b": 2},
        "test_auto",
        append=True,
    )

    content = u.rjb("test_auto")

    assert isinstance(content, dict), "Expected dict"
    assert content == {"a": 1, "b": 2}, f"Expected merged dict, got {content}"

    uw.p(f"Auto detected object mode: {content}")

    uw.p("")
    uw.ok("Auto mode test passed")

    safe_delete_json("test_auto")


def check_emit_text(value, expected_words):
    """Emit a value and verify expected words in the emitted text."""
    emitted = u.ejm(value)

    uw.p("")
    uw.p("Input value:")
    uw.p(value)

    uw.p("")
    uw.p("Emitted JSON mem result:")
    uw.p(emitted)

    assert emitted is not None, "Expected emitted output"

    emitted_text = str(emitted)

    for word in expected_words:
        assert word in emitted_text, f"Expected {word!r} in emitted result"

    return emitted


def test_emit_json_mem():
    """Test memory-only JSON emit with u.ejm()."""
    print_section("Test 5: Emit JSON Mem")

    dict_data = {
        "name": "Alice",
        "age": 30,
        "city": "Seoul",
        "active": True,
        "tags": ["json", "mem", "emit"],
        "profile": {
            "role": "tester",
            "level": 3,
        },
    }

    list_data = [
        {"name": "Alice", "score": 95},
        {"name": "Bob", "score": 88},
    ]

    scalar_data = "hello emit"

    # Current stable short alias:
    #   u.ejm() = emit json mem
    #
    # Planned full semantic form:
    #   use.emit.json.mem()
    #
    # Current note:
    #   use.emit.json.mem() may raise AttributeError
    #   until the "emit" branch is restored in the full-name router.
    check_emit_text(dict_data, ["Alice", "Seoul", "json", "tester"])
    check_emit_text(list_data, ["Alice", "Bob", "score"])
    check_emit_text(scalar_data, ["hello emit"])

    uw.p("")
    uw.ok("u.ejm emit json mem test passed")


def main():
    """Run all tests."""
    test_jsonl_append()
    test_array_append()
    test_object_append()
    test_auto_mode()
    test_emit_json_mem()

    uw.p("")
    uw.p("=" * 60)
    uw.ok("ALL TESTS PASSED")
    uw.p("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        uw.err(f"TEST FAILED: {exc}")
        raise
