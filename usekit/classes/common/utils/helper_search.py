# Path: usekit.classes.common.utils.helper_search.py
# -----------------------------------------------------------------------------------------------
#  A creation by: The Little Prince, in harmony with ROP and FOP
#  Generic data search utility (for txt/json/yaml/csv/... formats)
#  [MOBILE OPTIMIZED] Extension-based fast search (small file environment)
#  [ANY FORMAT SUPPORT] Smart format detection with mod-based filtering
#  [IMPROVED] Better extension handling for any format with helper_format support
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Union, List, Optional
from fnmatch import fnmatch
from usekit.classes.common.utils.helper_const import get_const, get_extension
from usekit.classes.common.utils.helper_path import get_smart_path, get_smart_path_list

# ───────────────────────────────────────────────────────────────
# [1] Pattern Matching Utility (Shared)
# ───────────────────────────────────────────────────────────────
def match_pattern(name: str, pattern: Union[str, list, tuple], case_sensitive: bool = False) -> bool:
    """
    Supports str, list, tuple pattern inputs with both glob (*) and SQL LIKE (%) syntax.
    
    Pattern types:
        - Glob style: test*, *.json, data*config
        - SQL LIKE style: test%, %.json, data%config (automatically converted to glob)
    """
    if not case_sensitive:
        name = name.lower()
    if isinstance(pattern, (list, tuple)):
        return any(match_pattern(name, p, case_sensitive) for p in pattern)
    elif isinstance(pattern, str):
        pat = pattern if case_sensitive else pattern.lower()
        # Convert SQL LIKE pattern (%) to glob pattern (*)
        pat = pat.replace('%', '*')
        return fnmatch(name, pat)
    else:
        raise TypeError("Invalid pattern type for 'pattern'.")

# ───────────────────────────────────────────────────────────────
# [2] Format Detection from Filename
# ───────────────────────────────────────────────────────────────
def detect_format_from_file(filepath: Union[str, Path]) -> Optional[str]:
    """
    Detect format type from file extension.
    
    This is a wrapper around helper_format.get_extension_from_file()
    for backward compatibility and convenience.
    
    Args:
        filepath: File path or filename
        
    Returns:
        Format type string (e.g., "json", "yaml", "txt") or None if unknown
        
    Example:
        detect_format_from_file("config.json")  # → "json"
        detect_format_from_file("/data/log.txt")  # → "txt"
        detect_format_from_file("data.unknown")  # → None
    """
    try:
        from usekit.classes.common.utils.helper_format import get_extension_from_file
        return get_extension_from_file(filepath)
    except ImportError:
        # Fallback using EXTENSION_MAP (parsers that actually exist)
        path = Path(filepath)
        ext = path.suffix.lower()
        
        if not ext:
            return None
        
        # Reverse lookup from EXTENSION_MAP
        ext_map = get_const("EXTENSION_MAP")
        for fmt, extension in ext_map.items():
            if extension == ext:
                return fmt
        
        return None

# ───────────────────────────────────────────────────────────────
# [3] Smart Extension List Builder (ANY format support)
# ───────────────────────────────────────────────────────────────
def build_extension_list(
    format_type: str,
    mod: Optional[str] = None,
    loc: Optional[str] = None,
    extensions: Optional[Union[str, List[str]]] = None
) -> List[str]:
    """
    Build extension list with smart format override and helper_format support.
    
    Logic:
        - Priority 1: Explicit extensions override everything
        - Priority 2: mod-based override for "any" format
        - Priority 3: Default format_type extension
        
    Args:
        format_type: Base format type ("any", "json", "txt", etc.)
        mod: Modifier format type (overrides format_type when fmt="any")
        extensions: Explicit extension list (highest priority)
        
    Returns:
        List of extensions (with leading dot)
        
    Example:
        build_extension_list("any", mod="json")  # → [".json"]
        build_extension_list("any", mod="all")   # → [".json", ".yaml", ".txt", ...]
        build_extension_list("txt")              # → [".txt"]
        build_extension_list("any", extensions=[".log", ".txt"])  # → [".log", ".txt"]
    """
    # Priority 1: Explicit extensions override everything
    if extensions:
        if isinstance(extensions, str):
            return [extensions if extensions.startswith(".") else "." + extensions]
        else:
            return [e if e.startswith(".") else "." + e for e in extensions]
    
    # Priority 2: mod-based override for "any" format
    if format_type == "any" and mod:
        if mod == "all":
            # Return all known extensions using helper_format
            try:
                from usekit.classes.common.utils.helper_format import get_all_extensions
                return get_all_extensions()
            except ImportError:
                # Fallback to const if helper_format not available
                ext_map = get_const("EXTENSION_MAP")
                return list(ext_map.values())
        else:
            # Use helper_format to get extension
            try:
                from usekit.classes.common.utils.helper_format import get_format_set
                ext = get_format_set(mod)
                return [ext] if ext else []
            except ImportError:
                # Fallback to get_extension if helper_format not available
                try:
                    ext = get_extension(mod)
                    return [ext]
                except:
                    return []
    
    # Priority 2.5:
    if loc == "cache" :
        format_type = "pkl"
        
    # Priority 3: Default format extension using helper_format
    try:
        from usekit.classes.common.utils.helper_format import get_format_set
        ext = get_format_set(format_type)
        return [ext]
    except ImportError:
        # Fallback to get_extension if helper_format not available
        try:
            ext = get_extension(format_type)
            return [ext]
        except:
            return []

# ───────────────────────────────────────────────────────────────
# [4] Generic Data Search (Improved)
# ───────────────────────────────────────────────────────────────
def find_data_search(
    format_type: str = "txt",
    mod: Optional[str] = None,
    pattern: str = "*",
    loc: str = "base",
    user_dir: str = None,
    cus: str = None,
    walk: bool = True,
    extensions: Optional[Union[str, List[str]]] = None,
    case_sensitive: bool = False,
    debug: bool = False
) -> List[Path]:
    """
    Smart file search with format-aware directory targeting.
    
    Args:
        format_type: Format type or "any" for cross-format search
        mod: Modifier for "any" format (format filter or "all")
        pattern: Filename pattern with smart wildcard handling
                 - "test" → "test.*" (matches test.json, test.yaml but NOT test123.json)
                 - "test*" → "test*" (matches test.json, test123.json, testing.log)
                 - "*test*" → "*test*" (explicit wildcards preserved)
                 - "test.json" → "test.json" (exact match with extension)
                 - "test%" → "test.*" (SQL LIKE converted)
        loc: Location type ("base", "sub", "tmp", etc.)
        walk: Recursive search (True) or top-level only (False)
        extensions: Explicit extension list (overrides format defaults)
        case_sensitive: Case-sensitive pattern matching
        debug: Print debug information
        
    Returns:
        List of matching Path objects
        
    Example:
        # Smart pattern: "config" finds config.json, config.yaml (NOT config_old.json)
        find_data_search("any", mod="all", pattern="config")
        
        # Prefix wildcard: "error*" finds error.log, error123.txt, error_2024.log
        find_data_search("any", mod="log", pattern="error*")
        
        # Exact match with extension
        find_data_search("json", pattern="config.json")
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] 탐색 디렉토리 결정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if format_type == "any" and mod == "all":
        # any + all: 모든 포맷 디렉토리 탐색
        search_dirs = get_smart_path_list(fmt="all", loc=loc,user_dir=user_dir)
        if debug:
            print(f"[DEBUG] Searching {len(search_dirs)} directories (any+all)")
        
    elif format_type == "any" and mod:
        # any + 특정 mod: any 디렉토리만
        base = get_smart_path(fmt="any", mod=mod, loc=loc, user_dir=user_dir, ensure_ext=False)
        search_dirs = [base]
        if debug:
            print(f"[DEBUG] Searching 1 directory (any+{mod}): {base}")
        
    else:
        # 일반 포맷: 해당 포맷 디렉토리만
        base = get_smart_path(fmt=format_type, loc=loc, user_dir=user_dir, ensure_ext=False)
        search_dirs = [base]
        if debug:
            print(f"[DEBUG] Searching 1 directory ({format_type}): {base}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] 확장자 필터 결정 (개선됨!)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ext_list = build_extension_list(format_type, mod, loc, extensions)
    
    if debug:
        print(f"[DEBUG] Extensions to search: {ext_list}")
    
    # 확장자가 없으면 파일명으로 검색
    search_by_filename = (not ext_list) or (format_type == "any" and mod == "all")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3] 각 디렉토리에서 탐색
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    all_files = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            if debug:
                print(f"[DEBUG] Directory not found: {search_dir}")
            continue
        
        if search_by_filename:
            # 확장자 없이 파일명으로 검색 (any + all 등)
            if walk:
                files = list(search_dir.rglob("*"))
            else:
                files = list(search_dir.glob("*"))
            # 파일만 필터링
            files = [f for f in files if f.is_file()]
            all_files.extend(files)
        else:
            # 확장자 기반 검색 (빠름!)
            for ext in ext_list:
                if walk:
                    files = search_dir.rglob(f"*{ext}")
                else:
                    files = search_dir.glob(f"*{ext}")
                all_files.extend(files)
    
    if debug:
        print(f"[DEBUG] Total files before pattern filter: {len(all_files)}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [4] 패턴 필터링
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    pattern_glob = pattern.replace("%", "*")  # SQL LIKE → glob
    
    # Smart pattern: "test" → "test.*" (unless already has wildcard or dot)
    if "*" not in pattern_glob and "?" not in pattern_glob:
        if "." not in pattern_glob:
            pattern_glob = pattern_glob + ".*"
    
    filtered = []
    for f in all_files:
        filename = f.name.lower() if not case_sensitive else f.name
        pattern_match = pattern_glob.lower() if not case_sensitive else pattern_glob
        
        if fnmatch(filename, pattern_match):
            filtered.append(f)
    
    if debug:
        print(f"[DEBUG] Found {len(filtered)} files matching '{pattern}'")
        if filtered and len(filtered) <= 10:
            for f in filtered:
                print(f"[DEBUG]   - {f}")
    
    return filtered


# ───────────────────────────────────────────────────────────────
# [5] Reverse Search: Get Format from Filename
# ───────────────────────────────────────────────────────────────
def find_format_from_name(filename: str) -> Optional[str]:
    """
    Quick format detection from filename (reverse search).
    
    This is the opposite of find_data_search:
        - find_data_search: format → files
        - find_format_from_name: file → format
    
    Args:
        filename: Filename or path
        
    Returns:
        Format type or None
        
    Example:
        find_format_from_name("config.json")    # → "json"
        find_format_from_name("data/test.yaml") # → "yaml"
        find_format_from_name("readme.txt")     # → "txt"
    """
    return detect_format_from_file(filename)