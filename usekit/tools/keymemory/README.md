# KeyMemory Package

`.km` (Key Memory) format parser and resolver for USEKIT framework

## Overview

KeyMemory provides hierarchical path management through `.km` format files, enabling:
- Anchor-based path references (`@BASE`, `@SRC`, etc.)
- Inheritance chains (`@CHILD = @PARENT/subpath`)
- Environment-independent path definitions
- Lightweight, mobile-friendly configuration

## Installation

Place the `keymemory` package in your project:
```
usekit/
└── tools/
        └── keymemory/
            ├── __init__.py
            ├── base.py
            └── parser.py
```

## .km Format Syntax

```km
# Comments start with #

# Level 1: Root anchors
@BASE = /content/drive/MyDrive/PROJECT
@ROOT = /home/user/project

# Level 2: Child anchors (inheritance)
@SRC = @BASE/src
@DATA = @BASE/data

# Level 3: Deep nesting
@MODELS = @SRC/models
@MODEL_CLS = @MODELS/classification

# Custom presets
@BLUE = @BASE/myfolder/blue
```

## Usage

### Basic Usage

```python
from keymemory import KeyMemory

# Load .km file
km = KeyMemory.load("config/paths.km")

# Resolve anchor to Path
path = km.resolve("@MODEL_CLS")
# Returns: PosixPath('/content/drive/MyDrive/PROJECT/src/models/classification')
```

### Dict-like Interface

```python
# Direct access
base_path = km["@BASE"]

# Get with default
temp_path = km.get("@TEMP", "/default/temp")

# Check existence
if "@MODELS" in km:
    models_path = km.resolve("@MODELS")

# Iterate
for anchor_name in km.keys():
    print(f"{anchor_name} -> {km[anchor_name]}")
```

### Integration with USEKIT

```python
from keymemory import KeyMemory

# Load project paths
km = KeyMemory.load(PROJECT_ROOT / ".usekit" / "paths.km")

# Use in get_smart_path()
def get_smart_path(fmt, mod, filename, loc):
    if filename.startswith("@"):
        anchor_part = filename.split(".")[0]  # "@MODEL_CLS"
        base_path = km.resolve(anchor_part)
        # ... rest of logic
```

## Features

### Inheritance Resolution

Automatically resolves nested references:
```km
@BASE = /project
@SRC = @BASE/src           # → /project/src
@MODELS = @SRC/models      # → /project/src/models
@CLS = @MODELS/cls         # → /project/src/models/cls
```

### Comment Support

```km
# This is a comment
@BASE = /project  # Inline comment also supported
```

### Error Handling

```python
# Missing anchor
try:
    path = km.resolve("@MISSING")
except KeyError as e:
    print(e)  # Shows available anchors

# Circular dependency detection
# @A = @B/sub
# @B = @A/sub
# Raises: ValueError with clear message
```

## API Reference

### KeyMemory Class

#### `KeyMemory.load(km_path)`
Load and parse `.km` file
- **Args**: `km_path` (str | Path) - Path to .km file
- **Returns**: KeyMemory instance
- **Raises**: FileNotFoundError, ValueError

#### `resolve(anchor_name)`
Resolve anchor to Path object
- **Args**: `anchor_name` (str) - Anchor name (e.g., '@BASE')
- **Returns**: Path object
- **Raises**: KeyError if anchor not found

#### `get(key, default=None)`
Dict-like get with default value
- **Args**: `key` (str), `default` (any)
- **Returns**: Anchor value or default

#### `keys()`, `values()`, `items()`
Standard dict-like iteration methods

### KMParser Class

#### `KMParser.parse_file(km_path)`
Parse .km file
- **Args**: `km_path` (str | Path)
- **Returns**: Dict of resolved anchors
- **Raises**: FileNotFoundError, ValueError

#### `KMParser.parse_line(line)`
Parse single line
- **Args**: `line` (str)
- **Returns**: (key, value) tuple or None

#### `KMParser.resolve_inheritance(raw_anchors)`
Resolve anchor inheritance chains
- **Args**: `raw_anchors` (Dict[str, str])
- **Returns**: Dict with resolved paths
- **Raises**: ValueError for circular dependencies

## Examples

### Example .km File

See `test_paths.km` for a complete example with:
- Root anchors
- Multi-level inheritance
- Custom presets
- Format-location aliases

### Example Test Suite

See `test_keymemory.py` for comprehensive examples:
- Line parsing
- Inheritance resolution
- File loading
- Dict interface
- Full resolution chains

## Future Phases

### Phase 2: Builder
- JSON export
- Tree visualization
- Data flattening

### Phase 3: Converter
- .km ↔ JSON conversion
- .km ↔ CSV conversion
- Format transformation

### Phase 4: Query
- Pattern matching
- Filtering
- Field selection

## Design Philosophy

KeyMemory follows USEKIT's "Memory-Oriented Architecture":
- **@ anchors**: Path pointers (stateful memory)
- **Inheritance**: DRY principle for paths
- **Simplicity**: Minimal syntax, maximum clarity
- **Mobile-first**: Lightweight config for bed coding

## Testing

Run the test suite:
```bash
python test_keymemory.py
```

Expected output:
- ✓ Parse line tests
- ✓ Inheritance resolution
- ✓ File loading
- ✓ Dict interface
- ✓ Full resolution chains

## Version

Current: 0.1.0 (Phase 1 - Parser + Base)

## License

Part of USEKIT framework
