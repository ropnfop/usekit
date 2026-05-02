# Path: usekit.classes.common.utils.helper_parse_pattern.py
# -----------------------------------------------------------------------------------------------
#  Pattern Parsing Helper - NO BLACK BOX!
#  Created by: THE Little Prince × ROP × FOP
#
#  Philosophy:
#  - Explicit is better than implicit
#  - Parse where you need it, not upstream
#  - No magic, no black box, just clear code
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from typing import Dict, Optional, Any


def should_parse_pattern(pattern: Optional[str]) -> bool:
    """
    Check if pattern needs parsing
    
    Detection Rules:
    ----------------
    ✅ Needs parsing if contains:
       - @ prefix: "@ps.utils", "@cs.data"
       - : suffix: "test:run", "module:function"
       - . in name: "aa.bb.cc", "utils.helpers"
    
    ❌ No parsing needed:
       - Simple name: "test", "config", "hello_use"
       - None or empty
    
    Args:
        pattern: Pattern string to check
    
    Returns:
        True if parsing needed, False otherwise
    
    Examples:
        >>> should_parse_pattern("test:run")
        True
        
        >>> should_parse_pattern("@ps.utils:run")
        True
        
        >>> should_parse_pattern("aa.bb.cc")
        True
        
        >>> should_parse_pattern("test")
        False
        
        >>> should_parse_pattern(None)
        False
    """
    if not pattern or not isinstance(pattern, str):
        return False
    
    pattern = pattern.strip()
    if not pattern:
        return False
    
    # Needs parsing if has special syntax
    return bool(
        pattern.startswith('@') or      # @ps.utils (inline codes)
        ':' in pattern or               # test:run (function suffix)
        '.' in pattern                  # aa.bb.cc (path dots)
    )


def parse_pattern(
    pattern: str,
    default_fmt: Optional[str] = None,
    default_loc: Optional[str] = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Parse pattern string into components
    
    Strategy:
    ---------
    1. Simple patterns (no @ or dots): Quick local parse
       "test:run" → name="test", func="run"
    
    2. Complex patterns (@ or dots): Delegate to params_value
       "@ps.utils:run" → use normalize_value_params()
       "aa.bb.cc:run" → use normalize_value_params()
    
    Args:
        pattern: Pattern string to parse
        default_fmt: Default format if not in pattern
        default_loc: Default location if not in pattern
        debug: Enable debug output
    
    Returns:
        Dict with parsed components:
        - name: Module/file name (leaf)
        - func: Function name (from :function suffix)
        - dir_path: Directory path (from aa.bb.cc dots)
        - ov_fmt: Format override (from @ps inline codes)
        - ov_loc: Location override (from @ps inline codes)
        - alias: Logical alias (from @ALIAS)
        - raw_pattern: Original pattern string
    
    Examples:
        >>> parse_pattern("test:run")
        {'name': 'test', 'func': 'run', 'raw_pattern': 'test:run'}
        
        >>> parse_pattern("@ps.utils:run")
        {
            'name': 'utils',
            'func': 'run',
            'ov_fmt': 'pyp',
            'ov_loc': 'sub',
            'raw_pattern': '@ps.utils:run'
        }
        
        >>> parse_pattern("aa.bb.cc:run")
        {
            'name': 'cc',
            'func': 'run',
            'dir_path': 'aa/bb',
            'raw_pattern': 'aa.bb.cc:run'
        }
    """
    if not pattern:
        return {}
    
    pattern = pattern.strip()
    result = {'raw_pattern': pattern}
    
    if debug:
        print(f"[PARSE] Pattern: {pattern}")
    
    # Determine parsing strategy
    has_at = pattern.startswith('@')
    has_dots = '.' in pattern.split(':', 1)[0]  # dots before colon
    
    # Strategy 1: Simple pattern (fast path)
    if not has_at and not has_dots:
        if debug:
            print(f"[PARSE] Strategy: SIMPLE (quick split)")
        return _parse_simple_pattern(pattern, result, debug)
    
    # Strategy 2: Complex pattern (delegate to params_value)
    if debug:
        print(f"[PARSE] Strategy: COMPLEX (use params_value)")
    return _parse_complex_pattern(pattern, result, debug)


def _parse_simple_pattern(
    pattern: str,
    result: Dict[str, Any],
    debug: bool = False
) -> Dict[str, Any]:
    """
    Quick parse for simple patterns: 'module:function'
    
    No external dependencies, just string split
    
    Examples:
        "test:run" → {'name': 'test', 'func': 'run'}
        "module" → {'name': 'module'}
    """
    if ':' in pattern:
        name, func = pattern.split(':', 1)
        result['name'] = name.strip()
        result['func'] = func.strip() or None
        
        if debug:
            print(f"[PARSE] Simple: name={result['name']}, func={result.get('func')}")
    else:
        result['name'] = pattern.strip()
        
        if debug:
            print(f"[PARSE] Simple: name={result['name']}")
    
    return result


def _parse_complex_pattern(
    pattern: str,
    result: Dict[str, Any],
    debug: bool = False
) -> Dict[str, Any]:
    """
    Complex pattern parsing via params_value
    
    Handles:
    - Inline codes: @ps → ov_fmt="pyp", ov_loc="sub"
    - Path dots: aa.bb.cc → dir_path="aa/bb", name="cc"
    - Logical alias: @SRC → alias="SRC"
    - Function suffix: :run → func="run"
    
    Examples:
        "@ps.utils:run" → uses params_value.normalize_value_params()
        "aa.bb.cc:run" → uses params_value.normalize_value_params()
    """
    try:
        from usekit.infra.params_value import normalize_value_params
        
        if debug:
            print(f"[PARSE] Calling params_value.normalize_value_params()")
        
        # Use params_value for complex parsing
        parsed = normalize_value_params(name=pattern)
        
        # Extract relevant fields
        for key in ['name', 'func', 'dir_path', 'ov_fmt', 'ov_loc', 'alias', 'raw_name']:
            if key in parsed and parsed[key] is not None:
                result[key] = parsed[key]
        
        if debug:
            print(f"[PARSE] Complex parsed: {result}")
        
        return result
    
    except ImportError as e:
        # Fallback if params_value not available
        if debug:
            print(f"[PARSE] WARNING: params_value not available, using simple parse")
            print(f"[PARSE] Error: {e}")
        
        return _parse_simple_pattern(pattern, result, debug)


def extract_pattern_components(
    pattern: Optional[str],
    name: Optional[str] = None,
    func: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    High-level helper: Extract components from pattern OR use explicit params
    
    Priority:
    ---------
    1. Explicit params (name, func, ov_fmt, ov_loc) - highest priority
    2. Pattern parsing - if pattern provided
    3. Defaults - if nothing provided
    
    Args:
        pattern: Pattern to parse (if needed)
        name: Explicit name (overrides pattern)
        func: Explicit func (overrides pattern)
        **kwargs: May contain ov_fmt, ov_loc, etc.
    
    Returns:
        Dict with final components after priority resolution
    
    Examples:
        >>> extract_pattern_components("test:run")
        {'name': 'test', 'func': 'run'}
        
        >>> extract_pattern_components("test:run", name="override")
        {'name': 'override', 'func': 'run'}
        
        >>> extract_pattern_components(name="test", func="run")
        {'name': 'test', 'func': 'run'}  # No parsing needed
    """
    # Check if already have everything (no parsing needed)
    has_explicit = bool(name or func or 'ov_fmt' in kwargs or 'ov_loc' in kwargs)
    
    if has_explicit:
        # Priority 1: Use explicit params
        result = {
            'name': name or pattern,
            'func': func,
        }
        
        # Add overrides if present
        if 'ov_fmt' in kwargs:
            result['ov_fmt'] = kwargs['ov_fmt']
        if 'ov_loc' in kwargs:
            result['ov_loc'] = kwargs['ov_loc']
        if 'dir_path' in kwargs:
            result['dir_path'] = kwargs['dir_path']
        
        return result
    
    # Priority 2: Parse pattern
    if pattern and should_parse_pattern(pattern):
        return parse_pattern(pattern, debug=kwargs.get('debug', False))
    
    # Priority 3: Simple name
    return {'name': pattern or name}


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    'should_parse_pattern',
    'parse_pattern',
    'extract_pattern_components',
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
