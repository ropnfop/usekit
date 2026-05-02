# Path: usekit.classes.data.base.load.ops.sub.dbl_common_sub.py
# -----------------------------------------------------------------------------------------------
#  Shared internal utilities for DATA operations
#  Used across read/write/update/delete/has procedures
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import os
import tempfile

# ────────────────────────────────────────────────
# [ Internal Utilities ]
# ────────────────────────────────────────────────

def _deep_merge_dict(base: dict, updates: dict) -> dict:
    """Deep merge two dictionaries recursively."""
    for k, v in updates.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge_dict(base[k], v)
        else:
            base[k] = v
    return base


def _ensure_path_obj(path):
    """Convert to Path object if needed."""
    return path if isinstance(path, Path) else Path(path)


def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Safe atomic write using temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _filter_dump_kwargs(fmt: str, for_file: bool = True, **kwargs) -> dict:
    """Filter kwargs to only include parameters supported by the format's dump function."""
    format_specific = {
        'json': ['indent', 'sort_keys', 'ensure_ascii', 'separators', 'wrap', 
                 'append', 'append_mode', 'overwrite', 'safe', 'encoding'],
        'yaml': ['indent', 'sort_keys', 'default_flow_style', 'width', 'allow_unicode'],
        'toml': ['indent', 'sort_keys'],
        'txt': [],
        'csv': ['delimiter', 'quotechar', 'quoting', 'lineterminator', 'escapechar'],
        'pkl': ['protocol', 'fix_imports'],
    }
    
    # Handle fmt="any" with mod parameter
    effective_fmt = fmt
    if fmt == "any":
        mod = kwargs.get('mod')
        if mod and mod in format_specific:
            effective_fmt = mod
        else:
            # Fallback for invalid/missing mod
            allowed = {'wrap', 'indent', 'sort_keys', 'ensure_ascii'}
            if for_file:
                allowed.add('encoding')
            return {k: v for k, v in kwargs.items() if k in allowed and k != 'mod'}
    
    allowed = set(format_specific.get(effective_fmt, []))
    
    if for_file and effective_fmt not in ('pkl',):
        allowed.add('encoding')
    
    return {k: v for k, v in kwargs.items() if k in allowed and k != 'mod'}


def _filter_load_kwargs(fmt: str, **kwargs) -> dict:
    """
    Filter kwargs to only include parameters supported by the format's load function.
    
    This includes read-specific options, especially TXT parser options like:
    - tail_*, regex, lines, strip (TXT only)
    - encoding (text formats)
    - unwrap_key, force_dict, return_meta (common)
    
    Note: 'wrap' is write-only (auto-wrap simple values), not for reading
    """
    format_specific = {
        'json': ['unwrap_key', 'force_dict', 'return_meta', 'encoding',
                 'jsonl', 'keydata', 'search_value', 'recursive', 'find_all',
                 'case_sensitive', 'regex', 'keydata_has'],
        'yaml': ['unwrap_key', 'force_dict', 'return_meta', 'encoding'],
        'txt': ['unwrap_key', 'force_dict', 'return_meta', 'encoding', 'newline',
                # TXT-specific read options
                'regex', 'invert_match', 'lines', 'line_numbers', 'strip', 'strip_empty',
                'tail_all', 'tail_top', 'tail_mid', 'tail_bottom',
                'append', 'append_newline', 'replace_all', 'max_count'],
        'csv': ['unwrap_key', 'force_dict', 'return_meta', 'encoding',
                'delimiter', 'quotechar', 'quoting', 'lineterminator', 'escapechar'],
        'pkl': ['unwrap_key', 'force_dict', 'return_meta',
                'protocol', 'fix_imports'],
        'md': ['unwrap_key', 'force_dict', 'return_meta', 'encoding'],
        'sql': ['unwrap_key', 'force_dict', 'return_meta', 'encoding'],
        'ddl': ['unwrap_key', 'force_dict', 'return_meta', 'encoding'],
    }
    
    # Handle fmt="any" with mod parameter
    effective_fmt = fmt
    if fmt == "any":
        mod = kwargs.get('mod')
        if mod and mod in format_specific:
            effective_fmt = mod
        else:
            # Fallback for invalid/missing mod
            common = ['unwrap_key', 'force_dict', 'return_meta', 'encoding']
            return {k: v for k, v in kwargs.items() if k in common and k != 'mod'}
    
    # Common params for unknown formats
    common = ['unwrap_key', 'force_dict', 'return_meta', 'encoding']
    allowed = set(format_specific.get(effective_fmt, common))
    
    return {k: v for k, v in kwargs.items() if k in allowed and k != 'mod'}


__all__ = [
    "_deep_merge_dict",
    "_ensure_path_obj",
    "_atomic_write_text",
    "_filter_dump_kwargs",
    "_filter_load_kwargs",
]

# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------