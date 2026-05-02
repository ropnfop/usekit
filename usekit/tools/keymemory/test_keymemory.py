# Path: usekit.tools.keymemory.test_keymemory.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# -----------------------------------------------------------------------------------------------

"""
Test KeyMemory parser and base class
"""

import sys
from pathlib import Path

# Import parser and base (simulate package import)
sys.path.insert(0, '/home/claude')
from keymemory_parser import KMParser
from keymemory_base import KeyMemory


def test_parser():
    """Test KMParser functionality"""
    print("=" * 60)
    print("TEST 1: KMParser.parse_line()")
    print("=" * 60)
    
    test_cases = [
        ("@BASE = /project", ('@BASE', '/project')),
        ("@SRC = @BASE/src", ('@SRC', '@BASE/src')),
        ("# comment", None),
        ("", None),
        ("@KEY = /path  # inline comment", ('@KEY', '/path')),
    ]
    
    for line, expected in test_cases:
        result = KMParser.parse_line(line)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{line}' -> {result}")
    
    print()


def test_inheritance():
    """Test inheritance resolution"""
    print("=" * 60)
    print("TEST 2: Inheritance Resolution")
    print("=" * 60)
    
    raw = {
        '@BASE': '/project',
        '@SRC': '@BASE/src',
        '@MODELS': '@SRC/models',
        '@MODEL_CLS': '@MODELS/classification'
    }
    
    resolved = KMParser.resolve_inheritance(raw)
    
    for key, value in resolved.items():
        print(f"{key:15} -> {value}")
    
    print()


def test_keymemory_load():
    """Test KeyMemory.load()"""
    print("=" * 60)
    print("TEST 3: KeyMemory.load()")
    print("=" * 60)
    
    km_path = Path("/home/claude/test_paths.km")
    km = KeyMemory.load(km_path)
    
    print(f"Loaded: {km}")
    print(f"Total anchors: {len(km)}")
    print()
    
    # Test specific resolutions
    test_anchors = [
        '@BASE',
        '@SRC',
        '@MODELS',
        '@MODEL_CLS',
        '@JSON_BASE',
        '@BLUE'
    ]
    
    for anchor in test_anchors:
        if anchor in km:
            path = km.resolve(anchor)
            print(f"{anchor:15} -> {path}")
    
    print()


def test_dict_interface():
    """Test dict-like interface"""
    print("=" * 60)
    print("TEST 4: Dict-like Interface")
    print("=" * 60)
    
    km = KeyMemory.load("/home/claude/test_paths.km")
    
    # __getitem__
    print(f"km['@BASE'] = {km['@BASE']}")
    
    # get with default
    print(f"km.get('@MISSING', 'default') = {km.get('@MISSING', 'default')}")
    
    # __contains__
    print(f"'@BASE' in km = {'@BASE' in km}")
    print(f"'@MISSING' in km = {'@MISSING' in km}")
    
    # keys, values, items
    print(f"\nFirst 5 keys: {list(km.keys())[:5]}")
    
    print()


def test_full_resolution():
    """Test full path resolution chain"""
    print("=" * 60)
    print("TEST 5: Full Resolution Chain")
    print("=" * 60)
    
    km = KeyMemory.load("/home/claude/test_paths.km")
    
    # Show full chain for deeply nested anchor
    anchor = '@MODEL_CLS'
    print(f"Anchor: {anchor}")
    print(f"Resolved: {km.resolve(anchor)}")
    print()
    
    # Show chain breakdown
    print("Resolution chain:")
    print("  @MODEL_CLS = @MODELS/classification")
    print("  @MODELS = @SRC/models")
    print("  @SRC = @BASE/src")
    print("  @BASE = /content/drive/MyDrive/PROJECT")
    print()
    print("Final result:")
    print(f"  {km.resolve(anchor)}")
    
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "KeyMemory Test Suite" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_parser()
        test_inheritance()
        test_keymemory_load()
        test_dict_interface()
        test_full_resolution()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
