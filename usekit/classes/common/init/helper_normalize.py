# Path: usekit.classes.common.init.helper_normalize.py
# -----------------------------------------------------------------------------------
#  Parameter Normalization Helper - Mobile-First Design
#  Created by: Little Prince × ROP × USEKIT
#
#  Philosophy:
#  - "Code is not function but memory"
#  - Normalize EVERYTHING: pattern + args + kwargs → clean params
#  - One source of truth for parameter handling
#
#  Usage:
#  ------
#  normalize("aa.bb.cc:run", *args, **kwargs)
#  normalize("@ps.utils:MyClass", base_path="/custom")
#  normalize(name="test", func="run", dir_path="@cs.data")
#
#  Why not helper_parse_pattern?
#  ------------------------------
#  Real-world usage requires FULL parameter normalization, not just pattern parsing:
#    u.exec("aa.bb.cc:run", *args, dir_path="@cs.data", custom=123)
#         ↑ pattern      ↑ args  ↑ kwargs conflict/merge
#
#  helper_parse_pattern can't handle:
#    - Priority: pattern vs explicit params vs defaults
#    - Merging: dir_path from pattern + dir_path from kwargs
#    - Alias normalization: nm→name, kd→keydata, fn→func
#
#  params_value.normalize_value_params does it all!
# -----------------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict

from usekit.infra.params_value import normalize_value_params


def normalize(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    Normalize all parameters: pattern + positional + keyword args
    
    This is the ONE function to use for parameter normalization in USEKIT.
    
    Features:
    ---------
    1. Pattern parsing:
       "aa.bb.cc:run" → name="cc", dir_path="aa/bb", func="run"
       "@ps.utils:run" → name="utils", ov_fmt="pyp", ov_loc="sub", func="run"
       "@SRC/module:fn" → name="module", alias="SRC", func="fn"
    
    2. Positional arg absorption:
       normalize("test:run", arg1, arg2) → name="test", func="run"
       First arg becomes 'name' if not explicitly provided
    
    3. Keyword arg normalization:
       nm → name, kd → keydata, fn → func, etc.
    
    4. Priority handling:
       - Pattern '@' wins: name="@ps.utils" overrides dir_path
       - dir_path '@' wins when pattern has no '@'
       - Explicit params override defaults
    
    5. Path merging:
       - If pattern has '@': dir_path from pattern REPLACES existing
       - If pattern has no '@': dir_path from pattern APPENDS to existing
    
    Args:
        *args: Positional arguments (first one becomes 'name' if not set)
        **kwargs: Keyword arguments (aliases normalized, values parsed)
    
    Returns:
        Normalized parameter dict with:
        - name: Single leaf name (file/module name)
        - func: Function/entry name (from :suffix)
        - dir_path: Directory path (dots → slashes)
        - alias: Logical alias (from @ALIAS)
        - ov_fmt: Format override (from @ps inline codes)
        - ov_loc: Location override (from @ps inline codes)
        - raw_name: Original expression (for debugging)
        - ... plus all other kwargs
    
    Examples:
        >>> normalize("aa.bb.cc:run")
        {'name': 'cc', 'dir_path': 'aa/bb', 'func': 'run', 'raw_name': 'aa.bb.cc:run'}
        
        >>> normalize("@ps.utils:run", custom=123)
        {
            'name': 'utils',
            'ov_fmt': 'pyp',
            'ov_loc': 'sub', 
            'func': 'run',
            'custom': 123,
            'raw_name': '@ps.utils:run'
        }
        
        >>> normalize("aa.bb.cc:run", dir_path="@cs.data")
        {
            'name': 'cc',
            'dir_path': 'data',  # dir_path '@' wins!
            'ov_fmt': 'csv',
            'ov_loc': 'sub',
            'func': 'run',
            'raw_name': 'aa.bb.cc:run'
        }
        
        >>> normalize(name="test", func="run", nm="override")
        {'name': 'override', 'func': 'run'}  # nm alias → name
    
    Mobile-First Optimization:
        - Fast path for simple cases (no pattern parsing overhead)
        - Comprehensive path for complex cases
        - All edge cases handled by battle-tested params_value
    
    See Also:
        - params_value.normalize_value_params: The underlying engine
        - params_alias.normalize_params: Key alias normalization
        - params_map: Format/location code mappings
    """
    return normalize_value_params(*args, **kwargs)


def normalize_pattern(pattern: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Convenience wrapper: normalize pattern with optional overrides
    
    Equivalent to normalize(name=pattern, **kwargs) but more explicit.
    
    Args:
        pattern: Pattern string to normalize
        **kwargs: Additional parameters (override pattern values)
    
    Returns:
        Normalized parameter dict
    
    Examples:
        >>> normalize_pattern("aa.bb.cc:run")
        {'name': 'cc', 'dir_path': 'aa/bb', 'func': 'run'}
        
        >>> normalize_pattern("test:run", func="override")
        {'name': 'test', 'func': 'override'}  # Explicit func wins
    """
    return normalize_value_params(name=pattern, **kwargs)


def normalize_exec_call(pattern: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    Normalize EXEC-layer call: pattern + args + kwargs
    
    Special handling for EXEC use cases where:
    - First arg is always the pattern/name
    - Remaining args are passed to the target
    - kwargs may contain both usekit params and target params
    
    Args:
        pattern: Target pattern (module.path:function)
        *args: Arguments to pass to target
        **kwargs: Mixed usekit + target parameters
    
    Returns:
        Normalized parameter dict with pattern parsed
    
    Examples:
        >>> normalize_exec_call("aa.bb.cc:run", 1, 2, 3, x=10)
        {
            'name': 'cc',
            'dir_path': 'aa/bb',
            'func': 'run',
            'raw_name': 'aa.bb.cc:run',
            # Note: *args and **kwargs for target are separate
        }
    
    Note:
        This doesn't handle target args/kwargs - that's EXEC layer's job.
        This ONLY normalizes the pattern + usekit parameters.
    """
    return normalize_value_params(name=pattern, **kwargs)


def quick_check_pattern(value: Any) -> bool:
    """
    Quick check: does value look like a pattern that needs normalization?
    
    Detection:
    ----------
    - Starts with '@': inline codes or alias
    - Contains ':': function suffix
    - Contains '.': path dots (before any ':')
    
    Args:
        value: Value to check
    
    Returns:
        True if normalization needed, False otherwise
    
    Examples:
        >>> quick_check_pattern("aa.bb.cc:run")
        True
        
        >>> quick_check_pattern("@ps.utils")
        True
        
        >>> quick_check_pattern("simple_name")
        False
        
        >>> quick_check_pattern(None)
        False
    
    Use Case:
        Fast pre-check to avoid normalization overhead for simple cases.
    """
    if not isinstance(value, str):
        return False
    
    value = value.strip()
    if not value:
        return False
    
    # Quick checks (order matters for performance)
    if value.startswith('@'):
        return True
    
    if ':' in value:
        return True
    
    # Check for dots before colon (path dots, not after :)
    colon_idx = value.find(':')
    if colon_idx == -1:
        # No colon, check entire string
        return '.' in value
    else:
        # Check only before colon
        return '.' in value[:colon_idx]


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    'normalize',
    'normalize_pattern', 
    'normalize_exec_call',
    'quick_check_pattern',
]


# -----------------------------------------------------------------------------------
#  Real-World Usage Examples
# -----------------------------------------------------------------------------------
#
#  Most Common Pattern (80% of usage):
#  ------------------------------------
#  u.xpb("test.test01:add", 10, 20)
#  u.xps("utils.math:calculate", x=5, y=10)
#  u.ipb("@ps.helpers.utils:MyClass", param1, param2)
#
#  How EXEC Layer Uses This:
#  --------------------------
#  def exec_ops(pattern, *target_args, **mixed_kwargs):
#      # Step 1: Normalize pattern + usekit params
#      params = normalize(pattern, **mixed_kwargs)
#      
#      # Step 2: Extract normalized components
#      name = params['name']              # "test01" from "test.test01:add"
#      func = params.get('func')          # "add"
#      dir_path = params.get('dir_path')  # "test"
#      fmt = params.get('ov_fmt', 'pyp')  # Format override or default
#      loc = params.get('ov_loc', 'base') # Location override or default
#      
#      # Step 3: Load module using normalized path
#      full_path = build_path(dir_path, name, fmt, loc)
#      module = load_module(full_path)
#      
#      # Step 4: Execute function with target args
#      target_func = getattr(module, func)
#      result = target_func(*target_args, **filter_target_kwargs(params))
#      
#      return result
#
#  Pattern Variations:
#  -------------------
#  # 1. Simple function call
#  normalize("test.test01:add")
#  # → {'name': 'test01', 'dir_path': 'test', 'func': 'add'}
#
#  # 2. With inline format/location codes
#  normalize("@ps.utils:helper")
#  # → {'name': 'utils', 'ov_fmt': 'pyp', 'ov_loc': 'sub', 'func': 'helper'}
#
#  # 3. With explicit dir_path override
#  normalize("test:run", dir_path="@cs.data")
#  # → {'name': 'test', 'dir_path': 'data', 'ov_fmt': 'csv', 
#  #    'ov_loc': 'sub', 'func': 'run'}
#
#  # 4. Deep nesting
#  normalize("aa.bb.cc.dd:process")
#  # → {'name': 'dd', 'dir_path': 'aa/bb/cc', 'func': 'process'}
#
#  # 5. Logical alias
#  normalize("@SRC/module:func")
#  # → {'name': 'module', 'alias': 'SRC', 'func': 'func'}
#
#  # 6. Mixed: inline + path + function
#  normalize("@ps.utils.helpers:MyClass")
#  # → {'name': 'helpers', 'dir_path': 'utils', 'ov_fmt': 'pyp',
#  #    'ov_loc': 'sub', 'func': 'MyClass'}
#
#  Parameter Separation Pattern:
#  -----------------------------
#  def exec_ops(pattern, *target_args, **mixed_kwargs):
#      # Normalize everything first
#      params = normalize(pattern, **mixed_kwargs)
#      
#      # USEKIT params (consumed by framework)
#      usekit_keys = {'name', 'func', 'dir_path', 'ov_fmt', 'ov_loc', 
#                     'alias', 'raw_name', 'fmt', 'loc', 'keydata'}
#      
#      # Target params (passed to user function)
#      target_kwargs = {k: v for k, v in params.items() 
#                       if k not in usekit_keys}
#      
#      # Execute
#      module = load_module(params)
#      func_obj = getattr(module, params['func'])
#      return func_obj(*target_args, **target_kwargs)
#
#  Mobile Coding Optimization:
#  ---------------------------
#  # Quick check to avoid overhead for simple names
#  if quick_check_pattern(pattern):
#      params = normalize(pattern, **kwargs)
#  else:
#      # Fast path: "simple_name" with no special chars
#      params = {'name': pattern, **kwargs}
#
#  Typical USEKIT Call Flow:
#  -------------------------
#  User types:
#      u.xpb("test.test01:add", 10, 20, debug=True)
#  
#  Framework does:
#      pattern = "test.test01:add"
#      target_args = (10, 20)
#      mixed_kwargs = {'debug': True}
#      
#      params = normalize(pattern, **mixed_kwargs)
#      # → {'name': 'test01', 'dir_path': 'test', 'func': 'add', 
#      #    'debug': True}
#      
#      # Load: /base/test/test01.pyp
#      # Call: test01.add(10, 20, debug=True)
#
# -----------------------------------------------------------------------------------
