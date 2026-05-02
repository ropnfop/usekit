# Path: usekit.infra.params_value.py
# -----------------------------------------------------------------------------------
#  High-level parameter value normalization for USEKIT
#
#  Core Responsibilities
#  ---------------------
#  1. Parse complex name expressions with multiple separators:
#     - "@" : alias/inline-code prefix
#     - ":" : function suffix separator 
#     - "." : path separator (converted to "/")
#     - "," : (reserved for future use - streaming/chaining)
#
#  2. Handle three main pattern types:
#     a) Module patterns:
#        - "test"           → name="test"
#        - "mytest.test"    → dir_path="mytest", name="test"
#     
#     b) Execution patterns:
#        - "test:run"       → name="test", func="run"
#        - "mytest.test:run"→ dir_path="mytest", name="test", func="run"
#     
#     c) Wildcard patterns:
#        - ":run"           → name="*", func="run"
#        - ":add"           → name="*", func="add"
#
#  3. Support inline codes and logical aliases:
#     - "@jb.data:run"    → inline: fmt="json", loc="base"
#     - "@SRC/path:run"   → logical: alias="SRC"
#
#  Stream Processing (Future)
#  ---------------------------
#  The "," separator is reserved for streaming/chaining operations:
#  - "data,transform"     → TBD: streaming pattern
#  - "data:load,process"  → TBD: function chaining
#
#  Role in USEKIT Architecture
#  ----------------------------
#  This module sits on top of `params_alias.normalize_params` and provides
#  "value-level" normalization. Results are consumed by:
#  - EXEC layer: execution context (name, func, dir_path)
#  - IMPORT layer: module loading (name, dir_path, alias)
#  - NAVI layer: navigation targets (name, dir_path, keydata)
#  - DATA layer: file I/O operations (fmt, loc, name)
#
#  Priority Rules
#  --------------
#  1. Name with "@" overrides dir_path completely
#  2. dir_path with "@" applies only when name has no "@"
#  3. Function suffix always parsed and stored as "func"
#  4. Empty target before ":" results in name="*" (wildcard)
#
#  Designed by: Little Prince × ROP × USEKIT
# -----------------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from usekit.infra.params_alias import normalize_params
from usekit.infra.params_map import FORMAT_CODES, LOCATION_CODES


NAME_SEP = ":"


def _parse_name_expr(expr: str) -> Dict[str, Optional[str]]:
    """
    Parse a combined name expression into components.

    Examples
    --------
    "@SRC/aa.bb.cc:run"
        raw_name  = "@SRC/aa.bb.cc:run"
        alias     = "SRC"
        target    = "aa.bb.cc"
        fn        = "run"

    "@jb.data/session01.task:run"
        raw_name  = "@jb.data/session01.task:run"
        alias     = "jb"                (inline code: j=json, b=base)
        target    = "data/session01.task"
        fn        = "run"

    "mytest.test:run"
        raw_name  = "mytest.test:run"
        alias     = None
        target    = "mytest.test"
        fn        = "run"
    
    ":run"
        raw_name  = ":run"
        alias     = None
        target    = None                (empty before colon)
        fn        = "run"
    
    "test"
        raw_name  = "test"
        alias     = None
        target    = "test"
        fn        = None

    Notes
    -----
    - Alias is extracted from "@" prefix (before first "/" or ".")
    - Target may be None for ":func" patterns (empty before colon)
    - Path normalization ("." to "/") happens in caller
    """
    raw = expr.strip()
    alias: Optional[str] = None
    target_part = raw
    fn: Optional[str] = None

    # 1) Split function suffix: "xxx:fn" → target_part="xxx", fn="fn"
    #    NOTE: ":fn" → target_part="", fn="fn" is valid!
    if NAME_SEP in raw:
        left, right = raw.rsplit(NAME_SEP, 1)
        target_part = left.strip()
        fn = right.strip() or None

    # 2) Extract leading "@ALIAS" or "@code" before first '/' or '.'
    if target_part.startswith("@"):
        body = target_part[1:]  # remove '@'
        cut = len(body)
        for i, ch in enumerate(body):
            if ch in ("/", "."):
                cut = i
                break

        alias = body[:cut] or None
        # remaining part after alias, strip leading '/' or '.'
        target_part = body[cut:].lstrip("/.")

    return {
        "raw_name": raw,
        "alias": alias,
        "target": target_part or None,  # May be None for ":func" patterns
        "fn": fn,
    }


def _apply_inline_codes(code: str, params: Dict[str, Any]) -> bool:
    """
    Interpret alias code as inline format/location spec.
    
    Order
    -----
    Position 0: format code (if valid)
    Position 1: location code (if valid)
    
    This matches the @obj.loc pattern:
      u.rjb() = read-json-base
               act-obj-loc
      @cs     = csv-sub
               obj-loc
    
    Example
    -------
    "@cs.data/path"  → code="cs"
      - code[0]='c' in FORMAT_CODES → ov_fmt="csv"
      - code[1]='s' in LOCATION_CODES → ov_loc="sub"
    
    Returns
    -------
    bool
        True if at least one code was applied, False otherwise.
    """
    used = False
    
    # Position 0: format
    if len(code) >= 1 and code[0] in FORMAT_CODES:
        params["ov_fmt"] = FORMAT_CODES[code[0]]
        used = True
    
    # Position 1: location
    if len(code) >= 2 and code[1] in LOCATION_CODES:
        params["ov_loc"] = LOCATION_CODES[code[1]]
        used = True
    
    return used


def _set_dir_path(params: Dict[str, Any], fragment: str, override: bool = False) -> None:
    """
    Update dir_path in params.

    Parameters
    ----------
    params : dict
        Parameter dict to modify.
    fragment : str
        Directory fragment (already normalized with '/' as separator).
    override : bool, default False
        - If True, always replace existing dir_path with `fragment`.
        - If False, append `fragment` to existing dir_path (if any),
          or set as new one.
    """
    if not fragment:
        return

    if override:
        params["dir_path"] = fragment
        return

    existing = params.get("dir_path")
    if isinstance(existing, str) and existing.strip():
        params["dir_path"] = f"{existing.rstrip('/')}/{fragment.lstrip('/')}"
    else:
        params["dir_path"] = fragment


def _split_target_into_dir_and_name(target: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize target path into (dir_fragment, leaf_name).

    Transformations
    ---------------
    - Replace all '.' with '/'
    - Split by '/'
    - Last segment becomes leaf name
    - Preceding segments become dir_fragment

    Examples
    --------
    "aa.bb.cc"      → ("aa/bb", "cc")
    "aa/bb.cc"      → ("aa/bb", "cc")
    "task"          → (None, "task")
    "" or None      → (None, None)
    """
    if not target:
        return None, None

    normalized = target.replace(".", "/")
    parts = [p for p in normalized.split("/") if p]

    if not parts:
        return None, None

    if len(parts) == 1:
        # only leaf, no directory
        return None, parts[0]

    dir_fragment = "/".join(parts[:-1])
    leaf = parts[-1]
    return dir_fragment, leaf


def normalize_value_params(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    High-level value normalization on top of `normalize_params`.

    Steps
    -----
    1) Absorb first positional argument as name if not provided
    2) Apply `normalize_params` (key alias: nm→name, kd→keydata, etc.)
    3) Parse name expression (if present):
         - raw_name : preserve original expression
         - alias    : "@xxx" prefix (without '@')
         - target   : part before ':' (may be None for ":func")
         - fn       : part after ':' (function suffix)
         
         NEW in v3.0.5:
         - SQL inline detection: check first non-empty line for SQL keywords
         - Multi-line content: skip ':' parsing for inline content
         - Handles both single-line and multi-line SQL statements
         
    4) Determine if alias is:
         - inline spec (fmt/loc codes) → ov_fmt/ov_loc override
         - logical alias → params["alias"]
    5) Process target part:
         - Convert dots to slashes
         - Split into dir_path + leaf name
         - If name has '@': dir_path from name overrides existing
         - If name has no '@': dir_path from name appends
         - SPECIAL: If target is None → name="*" (wildcard)
    6) Write function suffix as params["func"]
    7) Handle dir_path '@' priority (when name has no '@')

    Returns
    -------
    dict
        Normalized parameters ready for EXEC/IMPORT/NAVI/DATA layers
        
    Pattern Examples
    ----------------
    Module patterns (no function):
        "test"          → {'name': 'test', 'raw_name': 'test'}
        "mytest.test"   → {'dir_path': 'mytest', 'name': 'test', 'raw_name': 'mytest.test'}
    
    Execution patterns (with function):
        "test:run"      → {'name': 'test', 'func': 'run', 'raw_name': 'test:run'}
        "mytest.test:run" → {'dir_path': 'mytest', 'name': 'test', 'func': 'run', ...}
    
    Wildcard patterns (function-only):
        ":run"          → {'name': '*', 'func': 'run', 'raw_name': ':run'}
        ":add"          → {'name': '*', 'func': 'add', 'raw_name': ':add'}
    
    Inline code patterns:
        "@jb.data:run"  → {'ov_fmt': 'json', 'ov_loc': 'base', 'dir_path': 'data', ...}
    
    SQL inline patterns (NEW in v3.0.5):
        "SELECT * FROM users WHERE id = :user_id"
            → {'name': 'SELECT * FROM users WHERE id = :user_id', 'func': None}
            (Note: ':user_id' is NOT parsed as function, kept as SQL parameter)
        
        Multi-line SQL:
        '''
        SELECT id, name
        FROM users
        WHERE id = :user_id
        '''
            → {'name': '...full SQL...', 'func': None}
            (First non-empty line 'SELECT' triggers inline mode)
    """
    # Step 1: positional → name
    if args:
        if "name" not in kwargs and "nm" not in kwargs:
            kwargs = {"name": args[0], **kwargs}

    # Step 2: key alias normalization
    params = normalize_params(**kwargs)

    # Backup original dir_path for later priority logic
    orig_dir = params.get("dir_path")

    # Step 3: expression normalization on "name"
    name_val = params.get("name")
    if not (isinstance(name_val, str) and name_val.strip()):
        # No name to parse; we might still handle dir_path '@' later
        alias_code: Optional[str] = None
        fn: Optional[str] = None
    else:
        # ==========================================
        # NEW: Inline content detection (v3.0.5)
        # ==========================================
        should_parse = True  # Default: parse normally
        
        # Get first non-empty line for SQL keyword detection
        first_line = name_val.strip()
        if "\n" in name_val:
            # Multi-line content - check first non-empty line
            for line in name_val.split('\n'):
                stripped = line.strip()
                if stripped:
                    first_line = stripped
                    break
        
        # SQL inline detection (check first non-empty line)
        if params.get("fmt") == "sql":
            sql_keywords = (
                'SELECT', 'INSERT', 'UPDATE', 'DELETE', 
                'WITH', 'CREATE', 'DROP', 'ALTER'
            )
            first_line_upper = first_line.upper()
            is_sql_inline = any(
                first_line_upper.startswith(kw + ' ') or first_line_upper == kw
                for kw in sql_keywords
            )
            if is_sql_inline:
                should_parse = False
        
        # Multi-line content (non-SQL) → inline (don't parse)
        elif "\n" in name_val:
            should_parse = False
        
        # Process based on should_parse flag
        if not should_parse:
            # Inline content - keep name as-is, no parsing
            params.setdefault("raw_name", name_val)
            alias_code = None
            fn = None
        else:
            # Regular file pattern - parse normally
            parsed = _parse_name_expr(name_val)

            # Preserve original expression
            params.setdefault("raw_name", parsed["raw_name"])

            alias_code = parsed["alias"]
            target = parsed["target"]
            fn = parsed["fn"]

            # Step 4: alias handling (inline spec vs logical alias)
            inline_used = False
            if alias_code is not None:
                # If all characters are known format/location codes,
                # treat as inline spec instead of logical alias.
                if all((ch in FORMAT_CODES or ch in LOCATION_CODES) for ch in alias_code):
                    inline_used = _apply_inline_codes(alias_code, params)
                else:
                    # logical alias
                    params.setdefault("alias", alias_code)

            # Step 5: path handling for target (from name)
            if target:
                # Normal case: target exists (e.g., "test:run" or "mytest.test:run")
                dir_fragment, leaf = _split_target_into_dir_and_name(target)

                if dir_fragment:
                    override_mode = (alias_code is not None)
                    _set_dir_path(params, dir_fragment, override=override_mode)

                if leaf:
                    params["name"] = leaf
            else:
                # SPECIAL CASE: ":func" pattern (empty target before colon)
                # Example: ":run" → target=None → name="*", func="run"
                if fn is not None:
                    params["name"] = "*"

            # Step 6: function name ":xxx" → params["func"]
            if fn is not None:
                params.setdefault("func", fn)
            
    # Step 7: dir_path '@' priority when name has no alias
    #
    # Rules:
    #   - If name had no '@' (alias_code is None),
    #   - and original dir_path starts with '@',
    #     then dir_path expression wins over name-based dir_path.
    #
    # This allows patterns like:
    #   name="aa.bb.cc:run", dir_path="@js.data/session01"
    #   where dir_path provides alias/inline spec and directory.
    if isinstance(orig_dir, str):
        dir_str = orig_dir.strip()
        if dir_str.startswith("@"):
            # Only apply dir_path '@' override if name expression
            # did not carry its own alias.
            if "raw_name" in params:
                # We parsed a name expression above; alias_code is defined.
                # If alias_code is not None, name '@' has priority and
                # we do NOT override with dir_path '@'.
                if alias_code is not None:
                    return params

            # Either no name expression, or name had no '@'.
            parsed_dir = _parse_name_expr(dir_str)
            dir_alias_code = parsed_dir["alias"]
            dir_target = parsed_dir["target"]

            # Apply inline spec or logical alias from dir_path
            if dir_alias_code:
                if all(
                    (ch in FORMAT_CODES or ch in LOCATION_CODES)
                    for ch in dir_alias_code
                ):
                    _apply_inline_codes(dir_alias_code, params)
                else:
                    params.setdefault("alias", dir_alias_code)

            # dir_path from dir_target (dot → slash)
            if dir_target:
                dir_norm = dir_target.replace(".", "/")
                # dir_path from dir_path-expression overrides everything
                _set_dir_path(params, dir_norm, override=True)

    return params


__all__ = [
    "normalize_value_params",
]