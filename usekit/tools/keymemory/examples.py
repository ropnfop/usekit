# Path: usekit.tools.keymemory.examples.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# -----------------------------------------------------------------------------------------------

"""
KeyMemory Usage Examples

Demonstrates practical usage of KeyMemory package
"""

from pathlib import Path
from usekit.tools.keymemory.base import KeyMemory


def example_basic():
    """Example 1: Basic usage"""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Load .km file
    km = KeyMemory.load("test_paths.km")
    
    # Resolve anchors
    base = km.resolve("@BASE")
    src = km.resolve("@SRC")
    models = km.resolve("@MODELS")
    
    print(f"@BASE   -> {base}")
    print(f"@SRC    -> {src}")
    print(f"@MODELS -> {models}")
    print()


def example_dict_interface():
    """Example 2: Dict-like interface"""
    print("=" * 60)
    print("Example 2: Dict-like Interface")
    print("=" * 60)
    
    km = KeyMemory.load("test_paths.km")
    
    # Direct access
    print(f"km['@BASE'] = {km['@BASE']}")
    
    # Get with default
    custom = km.get("@CUSTOM", "/default/path")
    print(f"km.get('@CUSTOM', '/default/path') = {custom}")
    
    # Check membership
    print(f"'@SRC' in km = {'@SRC' in km}")
    
    # Iterate over anchors
    print(f"\nAll anchors ({len(km)} total):")
    for anchor in list(km.keys())[:5]:
        print(f"  {anchor:15} -> {km[anchor]}")
    print("  ...")
    print()


def example_usekit_integration():
    """Example 3: Integration with USEKIT get_smart_path()"""
    print("=" * 60)
    print("Example 3: USEKIT Integration")
    print("=" * 60)
    
    km = KeyMemory.load("test_paths.km")
    
    def get_smart_path(fmt, mod, filename, loc):
        """Simulated get_smart_path with KeyMemory support"""
        
        if filename.startswith("@"):
            # Parse anchor
            if "." in filename:
                anchor_part, rest = filename.split(".", 1)
            else:
                anchor_part = filename
                rest = ""
            
            # Resolve anchor
            if anchor_part in km:
                base_path = km.resolve(anchor_part)
                
                # Build full path
                if rest:
                    full_path = base_path / rest
                else:
                    full_path = base_path
                
                # Add extension
                if not full_path.suffix:
                    full_path = full_path.with_suffix(f".{fmt}")
                
                return full_path
        
        # Regular path handling
        return Path(f"/regular/{fmt}/{mod}_{loc}/{filename}.{fmt}")
    
    # Test cases
    test_cases = [
        ("json", "json", "@MODEL_CLS.train_data", "sub"),
        ("json", "json", "@BLUE.config", "sub"),
        ("pyp", "pyp", "regular_file", "base"),
    ]
    
    for fmt, mod, filename, loc in test_cases:
        result = get_smart_path(fmt, mod, filename, loc)
        print(f"get_smart_path('{fmt}', '{mod}', '{filename}', '{loc}')")
        print(f"  -> {result}")
    
    print()


def example_error_handling():
    """Example 4: Error handling"""
    print("=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)
    
    km = KeyMemory.load("test_paths.km")
    
    # Missing anchor
    try:
        path = km.resolve("@MISSING")
    except KeyError as e:
        print(f"✓ KeyError caught: {e}")
    
    # Safe access with get()
    path = km.get("@MISSING", Path("/default"))
    print(f"✓ Safe get: {path}")
    
    # Check before access
    if "@MODELS" in km:
        print(f"✓ Checked access: {km['@MODELS']}")
    
    print()


def example_custom_km_file():
    """Example 5: Creating custom .km file"""
    print("=" * 60)
    print("Example 5: Custom .km File")
    print("=" * 60)
    
    # Create custom .km file
    custom_km = """# Custom Project Paths
@PROJECT = /my/project
@SOURCE = @PROJECT/src
@DATA = @PROJECT/data
@OUTPUT = @PROJECT/output

# Data subdirectories
@RAW = @DATA/raw
@PROCESSED = @DATA/processed
@MODELS = @DATA/models

# Output subdirectories
@REPORTS = @OUTPUT/reports
@VISUALIZATIONS = @OUTPUT/viz
"""
    
    # Write to file
    custom_path = Path("custom_paths.km")
    custom_path.write_text(custom_km)
    
    # Load and use
    km = KeyMemory.load(custom_path)
    
    print("Custom .km file loaded:")
    for anchor in km.keys():
        print(f"  {anchor:20} -> {km[anchor]}")
    
    # Cleanup
    custom_path.unlink()
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 18 + "KeyMemory Examples" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    example_basic()
    example_dict_interface()
    example_usekit_integration()
    example_error_handling()
    example_custom_km_file()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
