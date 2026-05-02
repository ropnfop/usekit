# Path: usekit.classes.data.base.post.parser.parser_pyp.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Python source (pyp/py) parser - extends txt parser with Python structure parsing
# Features:
#   - Basic I/O: reuses txt parser (load/loads/dump/dumps)
#   - Python parsing: extract functions, classes, imports
#   - Structure analysis: key_type="def"/"class"/"import"/"all"
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Any, Union, Optional, List, Dict

# Reuse txt parser for basic I/O
from usekit.classes.data.base.post.parser.parser_txt import (
    load as txt_load,
    loads as txt_loads,
    dump as txt_dump,
    dumps as txt_dumps,
)

# Import Python-specific utilities
from usekit.classes.data.base.post.sub.parser_pyp_sub import (
    _extract_functions,
    _extract_classes,
    _extract_imports,
    _extract_docstring,
    _strip_docstring,
    _count_lines,
    _get_function_stats,
    _format_function,
    _format_class,
    _extract_function_dependencies,
    _extract_function_with_imports,
    _parse_module_spec,
    _validate_function_exists,
    _build_executable_block,
    _build_executable_with_variables,
    _extract_module_variables,
)


# ===============================================================================
# Helper Functions
# ===============================================================================

def _filter_blocks_by_name(
    blocks: List[Dict],
    pattern: str,
    regex: bool = False,
    case_sensitive: bool = False
) -> List[Dict]:
    """
    Filter blocks by name pattern.
    
    Args:
        blocks: List of block dicts
        pattern: Search pattern
        regex: Use regex matching
        case_sensitive: Case-sensitive matching
        
    Returns:
        Filtered list of blocks
    """
    import re as re_module
    
    if not pattern:
        return blocks
    
    filtered = []
    
    for block in blocks:
        name = block.get("name", "")
        
        if regex:
            # Regex matching
            flags = 0 if case_sensitive else re_module.IGNORECASE
            try:
                if re_module.search(pattern, name, flags):
                    filtered.append(block)
            except re_module.error:
                # Invalid regex, fall back to substring
                if case_sensitive:
                    if pattern in name:
                        filtered.append(block)
                else:
                    if pattern.lower() in name.lower():
                        filtered.append(block)
        else:
            # Simple substring matching
            if case_sensitive:
                if pattern in name:
                    filtered.append(block)
            else:
                if pattern.lower() in name.lower():
                    filtered.append(block)
    
    return filtered


# ===============================================================================
# Main Interface Functions
# ===============================================================================

def load(
    file: Union[str, Path],
    *,
    encoding: str = "utf-8",
    lines: bool = False,
    strip: bool = False,
    key_type: Optional[str] = None,
    keydata: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    include_body: bool = True,
    include_decorators: bool = True,
    **kwargs
) -> Union[str, List, Dict]:
    """
    Load Python source file with optional structure parsing and filtering.
    
    Basic Usage:
        code = load("script.py")                    # Read as plain text
        lines = load("script.py", lines=True)       # Read as line list
        code = load("script.py", strip=True)        # Strip whitespace
    
    Python Structure Parsing:
        funcs = load("script.py", key_type="def")       # Extract all functions
        classes = load("script.py", key_type="class")   # Extract all classes
        imports = load("script.py", key_type="import")  # Extract all imports
        all_blocks = load("script.py", key_type="all")  # Extract everything
    
    Function Filtering (key_type + keydata):
        funcs = load("script.py", key_type="def", keydata="process")  # Functions with "process" in name
        funcs = load("script.py", key_type="def", keydata="^test_", regex=True)  # Test functions
        funcs = load("script.py", key_type="def", keydata="Helper", case_sensitive=True)  # Exact match
    
    Text Search (keydata only):
        result = load("script.py", keydata="TODO")  # Search lines (uses txt parser)
    
    Options:
        funcs = load("script.py", key_type="def", include_body=False)  # Signatures only
        funcs = load("script.py", key_type="def", include_decorators=False)  # No decorators
    
    Args:
        file: File path
        
        encoding: File encoding
        lines: Return as list of lines (plain text mode)
        strip: Strip whitespace (plain text mode)
        
        key_type: Python structure to extract - "def"/"class"/"import"/"all"/None
        keydata: Filter pattern - searches in names (if key_type) or in lines (if no key_type)
        regex: Use regex for keydata matching
        case_sensitive: Case-sensitive keydata matching
        
        include_body: Include function/class body in extracted blocks
        include_decorators: Include decorator lines in extracted blocks
        
    Returns:
        - If key_type=None: string or list (plain text)
        - If key_type specified: list of dicts with structure info (filtered by keydata)
    """
    
    # Read content using txt parser
    content = txt_load(file, encoding=encoding)
    
    # Plain text mode (no key_type)
    if key_type is None:
        # If keydata provided, use txt parser's search
        if keydata:
            return txt_load(
                file, 
                encoding=encoding, 
                keydata=keydata,
                regex=regex,
                case_sensitive=case_sensitive,
                lines=lines,
                **kwargs
            )
        
        # Plain read
        if strip:
            content = content.strip()
        if lines:
            result = content.splitlines()
            if strip:
                result = [line.strip() for line in result]
            return result
        return content
    
    # Python structure parsing mode
    if key_type == "def" or key_type == "function":
        blocks = _extract_functions(
            content,
            include_async=True,
            include_decorators=include_decorators,
            include_docstring=include_body,
            include_body=include_body
        )
    elif key_type == "class":
        blocks = _extract_classes(
            content,
            include_methods=True,
            include_decorators=include_decorators,
            include_docstring=include_body
        )
    elif key_type == "import":
        blocks = _extract_imports(content)
    elif key_type == "all":
        # Combine all types
        blocks = {
            "functions": _extract_functions(content),
            "classes": _extract_classes(content),
            "imports": _extract_imports(content)
        }
    else:
        raise ValueError(f"Invalid key_type: {key_type}. Use 'def', 'class', 'import', or 'all'")
    
    # Apply keydata filtering if provided
    if keydata and isinstance(blocks, list):
        blocks = _filter_blocks_by_name(blocks, keydata, regex, case_sensitive)
    elif keydata and isinstance(blocks, dict):
        # Filter each category
        for key in blocks:
            if isinstance(blocks[key], list):
                blocks[key] = _filter_blocks_by_name(blocks[key], keydata, regex, case_sensitive)
    
    return blocks


def loads(
    text: str,
    *,
    lines: bool = False,
    strip: bool = False,
    key_type: Optional[str] = None,
    keydata: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    include_body: bool = True,
    include_decorators: bool = True,
    **kwargs
) -> Union[str, List, Dict]:
    """
    Parse Python source string with optional structure parsing and filtering.
    
    Basic Usage:
        code = loads(text)                          # Return as-is
        lines = loads(text, lines=True)             # Split to lines
        code = loads(text, strip=True)              # Strip whitespace
    
    Python Structure Parsing:
        funcs = loads(text, key_type="def")         # Extract functions
        classes = loads(text, key_type="class")     # Extract classes
        imports = loads(text, key_type="import")    # Extract imports
        all_blocks = loads(text, key_type="all")    # Extract everything
    
    Function Filtering:
        funcs = loads(text, key_type="def", keydata="helper")  # Functions with "helper" in name
        funcs = loads(text, key_type="def", keydata="^_", regex=True)  # Private functions
    
    Text Search:
        result = loads(text, keydata="TODO")  # Search lines (uses txt parser)
    
    Args:
        text: Python source code string
        
        lines: Return as list of lines (plain text mode)
        strip: Strip whitespace (plain text mode)
        
        key_type: Python structure to extract
        keydata: Filter pattern - searches in names (if key_type) or in lines (if no key_type)
        regex: Use regex for keydata matching
        case_sensitive: Case-sensitive keydata matching
        
        include_body: Include function/class body
        include_decorators: Include decorators
        
    Returns:
        String, list, or list of dicts
    """
    
    # Plain text mode (no key_type)
    if key_type is None:
        # If keydata provided, use txt parser's search
        if keydata:
            return txt_loads(
                text,
                keydata=keydata,
                regex=regex,
                case_sensitive=case_sensitive,
                lines=lines,
                **kwargs
            )
        
        # Plain read
        if strip:
            text = text.strip()
        if lines:
            result = text.splitlines()
            if strip:
                result = [line.strip() for line in result]
            return result
        return text
    
    # Python structure parsing mode
    if key_type == "def" or key_type == "function":
        blocks = _extract_functions(
            text,
            include_async=True,
            include_decorators=include_decorators,
            include_docstring=include_body,
            include_body=include_body
        )
    elif key_type == "class":
        blocks = _extract_classes(
            text,
            include_methods=True,
            include_decorators=include_decorators,
            include_docstring=include_body
        )
    elif key_type == "import":
        blocks = _extract_imports(text)
    elif key_type == "all":
        # Combine all types
        blocks = {
            "functions": _extract_functions(text),
            "classes": _extract_classes(text),
            "imports": _extract_imports(text)
        }
    else:
        raise ValueError(f"Invalid key_type: {key_type}. Use 'def', 'class', 'import', or 'all'")
    
    # Apply keydata filtering if provided
    if keydata and isinstance(blocks, list):
        blocks = _filter_blocks_by_name(blocks, keydata, regex, case_sensitive)
    elif keydata and isinstance(blocks, dict):
        # Filter each category
        for key in blocks:
            if isinstance(blocks[key], list):
                blocks[key] = _filter_blocks_by_name(blocks[key], keydata, regex, case_sensitive)
    
    return blocks


def dump(
    data: Any,
    file: Union[str, Path],
    *,
    encoding: str = "utf-8",
    newline: Optional[str] = None,
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    append_newline: bool = True,
    **kwargs
) -> None:
    """
    Write Python source to file (delegates to txt parser).
    
    Basic Usage:
        dump("print('hello')", "script.py")                 # Write code
        dump(code, "script.py", append=True)                # Append code
        dump(code, "script.py", safe=False)                 # Fast write
        dump(code, "script.py", overwrite=False)            # Fail if exists
    
    Block Formatting:
        blocks = load("old.py", key_type="def")
        for block in blocks:
            formatted = _format_python_block(block)
            dump(formatted, "new.py", append=True)
    
    Args:
        data: Python source code (string or auto-convert with wrap=True)
        file: File path
        
        encoding: File encoding
        newline: Newline mode
        
        wrap: Auto-convert non-strings
        overwrite: Allow overwriting
        safe: Use atomic write
        append: Append mode
        append_newline: Add newline before appending
        
    Returns:
        None
    """
    
    return txt_dump(
        data, file,
        encoding=encoding,
        newline=newline,
        wrap=wrap,
        overwrite=overwrite,
        safe=safe,
        append=append,
        append_newline=append_newline,
        **kwargs
    )


def dumps(
    data: Any,
    *,
    wrap: bool = False,
    **kwargs
) -> str:
    """
    Serialize to string (delegates to txt parser).
    
    Args:
        data: Data to convert
        wrap: Auto-convert non-strings
        
    Returns:
        String representation
    """
    
    return txt_dumps(data, wrap=wrap, **kwargs)


# ===============================================================================
# Convenience Functions
# ===============================================================================

def get_functions(file: Union[str, Path], encoding: str = "utf-8") -> List[str]:
    """
    Quick helper: get list of function names from file.
    
    Args:
        file: Python file path
        encoding: File encoding
        
    Returns:
        List of function names
    """
    content = txt_load(file, encoding=encoding)
    funcs = _extract_functions(content)
    return [f["name"] for f in funcs]


def get_classes(file: Union[str, Path], encoding: str = "utf-8") -> List[str]:
    """
    Quick helper: get list of class names from file.
    
    Args:
        file: Python file path
        encoding: File encoding
        
    Returns:
        List of class names
    """
    content = txt_load(file, encoding=encoding)
    classes = _extract_classes(content)
    return [c["name"] for c in classes]


def get_function_stats(file: Union[str, Path], encoding: str = "utf-8") -> List[Dict]:
    """
    Get statistics for all functions in file.
    
    Args:
        file: Python file path
        encoding: File encoding
        
    Returns:
        List of function statistics dicts
    """
    content = txt_load(file, encoding=encoding)
    funcs = _extract_functions(content)
    return [_get_function_stats(f) for f in funcs]


def format_block(block: Dict, include_body: bool = True) -> str:
    """
    Format extracted Python block back to source code.
    
    Args:
        block: Block dict from load(..., key_type=...)
        include_body: Include function/class body
        
    Returns:
        Formatted source code
    """
    if block.get("type") == "class" or "methods" in block:
        return _format_class(block, include_methods=include_body)
    else:
        return _format_function(block, include_body=include_body)


def extract_executable(
    file: Union[str, Path],
    func_names: Union[str, List[str]],
    *,
    encoding: str = "utf-8",
    include_imports: bool = True,
    include_decorators: bool = True
) -> str:
    """
    Extract functions/variables/classes as executable code block.
    
    This function intelligently extracts:
    - Functions (def/async def)
    - Module-level variables (e.g., uw = WatchHandler())
    - Classes
    
    Args:
        file: Python file path
        func_names: Single name or list of names to extract
        encoding: File encoding
        include_imports: Include required imports
        include_decorators: Include decorators
        
    Returns:
        Executable Python code string
        
    Examples:
        # Single function
        code = extract_executable("utils.py", "helper")
        exec(code)
        
        # Multiple functions
        code = extract_executable("utils.py", ["fn1", "fn2", "fn3"])
        exec(code)
        
        # Module variable (singleton)
        code = extract_executable("watch.py", "uw")
        exec(code)  # Now uw is available
        
        # Mixed: functions + variables + classes
        code = extract_executable("module.py", ["func1", "var1", "Class1"])
        exec(code)
    """
    
    content = txt_load(file, encoding=encoding)
    
    # Normalize to list
    if isinstance(func_names, str):
        func_names = [func_names]
    
    # Use the new unified builder that handles functions, variables, and classes
    return _build_executable_with_variables(
        content,
        names=func_names,
        include_decorators=include_decorators,
        include_imports=include_imports
    )


def parse_spec(spec: str) -> Dict:
    """
    Parse module specification for use.exec.pyp.base().
    
    Args:
        spec: Module spec string
        
    Returns:
        Parsed specification dict
        
    Examples:
        parse_spec("helpers.data:clean_text")
        # {"module_path": "helpers.data", "functions": ["clean_text"]}
        
        parse_spec("utils:fn1,fn2,fn3")
        # {"module_path": "utils", "functions": ["fn1", "fn2", "fn3"]}
    """
    return _parse_module_spec(spec)


def validate_spec(
    file: Union[str, Path],
    func_names: List[str],
    encoding: str = "utf-8"
) -> Dict:
    """
    Validate that functions exist in file.
    
    Args:
        file: Python file path
        func_names: List of function names to validate
        encoding: File encoding
        
    Returns:
        Validation results dict with "valid" and "missing" keys
        
    Example:
        result = validate_spec("utils.py", ["fn1", "fn2", "missing"])
        # {"valid": ["fn1", "fn2"], "missing": ["missing"]}
    """
    
    content = txt_load(file, encoding=encoding)
    return _validate_function_exists(content, func_names)


def extract_with_deps(
    file: Union[str, Path],
    func_name: str,
    *,
    encoding: str = "utf-8",
    include_decorators: bool = True
) -> Optional[Dict]:
    """
    Extract single function with its dependencies.
    
    Args:
        file: Python file path
        func_name: Function name to extract
        encoding: File encoding
        include_decorators: Include decorators
        
    Returns:
        Dict with function info, imports, and executable code
        
    Example:
        info = extract_with_deps("utils.py", "process_data")
        # {
        #   "function": {...},
        #   "imports": ["from pathlib import Path", ...],
        #   "executable_code": "from pathlib import Path\n\ndef process_data(...):\n..."
        # }
        
        # Execute it
        exec(info["executable_code"])
    """
    
    content = txt_load(file, encoding=encoding)
    return _extract_function_with_imports(content, func_name, include_decorators)


# ===============================================================================
# Test Helper
# ===============================================================================

def _test(base="sample.py"):
    """Test PYP parser functionality."""
    
    print("\n=== Basic I/O Tests ===")
    
    # Test code
    test_code = '''
@decorator
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello {name}"

class MyClass:
    """A test class."""
    def __init__(self):
        self.value = 42
    
    def method(self):
        return self.value

def goodbye():
    print("Bye")
'''
    
    # 1) Write
    dump(test_code, base)
    print(f"[1] Wrote Python code to {base}")
    
    # 2) Read plain
    code = load(base)
    print(f"[2] Read plain: {len(code)} chars")
    
    # 3) Read lines
    lines = load(base, lines=True)
    print(f"[3] Read lines: {len(lines)} lines")
    
    print("\n=== Python Structure Parsing ===")
    
    # 4) Extract functions
    funcs = load(base, key_type="def")
    print(f"[4] Extracted {len(funcs)} functions:")
    for f in funcs:
        print(f"    - {f['name']} (lines {f['line_start']}-{f['line_end']})")
    
    # 5) Extract classes
    classes = load(base, key_type="class")
    print(f"[5] Extracted {len(classes)} classes:")
    for c in classes:
        print(f"    - {c['name']}")
    
    # 6) Quick helpers
    func_names = get_functions(base)
    class_names = get_classes(base)
    print(f"[6] Quick extraction:")
    print(f"    Functions: {func_names}")
    print(f"    Classes: {class_names}")
    
    # 7) Extract signatures only
    sigs = load(base, key_type="def", include_body=False)
    print(f"[7] Function signatures only:")
    for s in sigs:
        print(f"    {s['signature']}")
    
    print("\n=== Cleanup ===")
    Path(base).unlink(missing_ok=True)
    print(f"Removed {base}")


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "load",
    "loads",
    "dump",
    "dumps",
    "get_functions",
    "get_classes",
    "get_function_stats",
    "format_block",
    "extract_executable",
    "parse_spec",
    "validate_spec",
    "extract_with_deps",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
