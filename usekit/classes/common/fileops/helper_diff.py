# Path: usekit.classes.common.fileops.helper_diff.py
# -----------------------------------------------------------------------------------------------
#  Diff Utilities - Show differences before operations
#  Created by: THE Little Prince × ROP × FOP
#  
#  Philosophy:
#  - Preview changes before executing update operations
#  - Support multiple data formats (JSON, text, files)
#  - Clear visualization of added/removed/modified content
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


# ===============================================================================
# File Diff
# ===============================================================================

def diff_files(
    old_file: Path,
    new_file: Path,
    context_lines: int = 3
) -> str:
    """
    Show differences between two files.
    
    Uses unified diff format.
    
    Args:
        old_file: Original file
        new_file: New file
        context_lines: Number of context lines to show
        
    Returns:
        Diff output string (unified diff format)
        
    Examples:
        >>> diff = diff_files(Path("old.txt"), Path("new.txt"))
        >>> print(diff)
        --- old.txt
        +++ new.txt
        @@ -1,3 +1,3 @@
         line 1
        -old line
        +new line
         line 3
    """
    import difflib
    
    try:
        with open(old_file, 'r', encoding='utf-8') as f1:
            old_lines = f1.readlines()
        
        with open(new_file, 'r', encoding='utf-8') as f2:
            new_lines = f2.readlines()
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(old_file),
            tofile=str(new_file),
            lineterm='',
            n=context_lines
        )
        
        return '\n'.join(diff)
    
    except Exception as e:
        return f"Error reading files: {e}"


# ===============================================================================
# JSON Diff
# ===============================================================================

def diff_json(
    old_data: Union[dict, list],
    new_data: Union[dict, list],
    path: str = ""
) -> Dict[str, Dict]:
    """
    Show differences between two JSON objects.
    
    Recursively compares nested structures.
    
    Args:
        old_data: Original data
        new_data: New data
        path: Current path (for recursion)
        
    Returns:
        {
            'added': {path: value, ...},
            'removed': {path: value, ...},
            'modified': {path: {'old': old_val, 'new': new_val}, ...}
        }
        
    Examples:
        >>> old = {'user': {'name': 'Alice', 'age': 25}}
        >>> new = {'user': {'name': 'Alice', 'age': 26, 'email': 'alice@example.com'}}
        >>> diff = diff_json(old, new)
        >>> diff['added']
        {'user.email': 'alice@example.com'}
        >>> diff['modified']
        {'user.age': {'old': 25, 'new': 26}}
    """
    added = {}
    removed = {}
    modified = {}
    
    # Handle dict
    if isinstance(old_data, dict) and isinstance(new_data, dict):
        # Check all keys in new
        for key in new_data:
            new_path = f"{path}.{key}" if path else key
            
            if key not in old_data:
                # Key added
                added[new_path] = new_data[key]
            elif old_data[key] != new_data[key]:
                # Value changed
                if isinstance(old_data[key], (dict, list)) and isinstance(new_data[key], (dict, list)):
                    # Recurse into nested structure
                    sub_diff = diff_json(old_data[key], new_data[key], new_path)
                    added.update(sub_diff['added'])
                    removed.update(sub_diff['removed'])
                    modified.update(sub_diff['modified'])
                else:
                    # Simple value changed
                    modified[new_path] = {
                        'old': old_data[key],
                        'new': new_data[key]
                    }
        
        # Check removed keys
        for key in old_data:
            if key not in new_data:
                old_path = f"{path}.{key}" if path else key
                removed[old_path] = old_data[key]
    
    # Handle list
    elif isinstance(old_data, list) and isinstance(new_data, list):
        old_len = len(old_data)
        new_len = len(new_data)
        
        # Compare common indices
        for i in range(min(old_len, new_len)):
            idx_path = f"{path}[{i}]" if path else f"[{i}]"
            
            if old_data[i] != new_data[i]:
                if isinstance(old_data[i], (dict, list)) and isinstance(new_data[i], (dict, list)):
                    # Recurse into nested
                    sub_diff = diff_json(old_data[i], new_data[i], idx_path)
                    added.update(sub_diff['added'])
                    removed.update(sub_diff['removed'])
                    modified.update(sub_diff['modified'])
                else:
                    modified[idx_path] = {
                        'old': old_data[i],
                        'new': new_data[i]
                    }
        
        # Handle added items
        if new_len > old_len:
            for i in range(old_len, new_len):
                idx_path = f"{path}[{i}]" if path else f"[{i}]"
                added[idx_path] = new_data[i]
        
        # Handle removed items
        if old_len > new_len:
            for i in range(new_len, old_len):
                idx_path = f"{path}[{i}]" if path else f"[{i}]"
                removed[idx_path] = old_data[i]
    
    # Different types
    else:
        if path:
            modified[path] = {
                'old': old_data,
                'new': new_data
            }
    
    return {
        'added': added,
        'removed': removed,
        'modified': modified
    }


# ===============================================================================
# Diff Display
# ===============================================================================

def show_diff(
    diff_result: Dict[str, Dict],
    format: str = "simple",
    max_value_len: int = 80
) -> None:
    """
    Display diff in readable format.
    
    Args:
        diff_result: Output from diff_json()
        format: Display format ("simple", "detailed", "compact")
        max_value_len: Maximum value length to display
        
    Examples:
        >>> diff = diff_json(old_data, new_data)
        >>> show_diff(diff)
        
        [ADDED]
          + user.email: alice@example.com
          + settings.theme: dark
        
        [REMOVED]
          - user.old_field: value
        
        [MODIFIED]
          ~ user.age:
              old: 25
              new: 26
    """
    def format_value(value):
        """Format value for display."""
        value_str = str(value)
        if len(value_str) > max_value_len:
            return value_str[:max_value_len] + "..."
        return value_str
    
    has_changes = False
    
    # Show added
    if diff_result.get('added'):
        has_changes = True
        print("\n[ADDED]")
        for path, value in sorted(diff_result['added'].items()):
            if format == "compact":
                print(f"  + {path}")
            else:
                print(f"  + {path}: {format_value(value)}")
    
    # Show removed
    if diff_result.get('removed'):
        has_changes = True
        print("\n[REMOVED]")
        for path, value in sorted(diff_result['removed'].items()):
            if format == "compact":
                print(f"  - {path}")
            else:
                print(f"  - {path}: {format_value(value)}")
    
    # Show modified
    if diff_result.get('modified'):
        has_changes = True
        print("\n[MODIFIED]")
        for path, change in sorted(diff_result['modified'].items()):
            if format == "compact":
                print(f"  ~ {path}")
            elif format == "simple":
                print(f"  ~ {path}:")
                print(f"      old: {format_value(change['old'])}")
                print(f"      new: {format_value(change['new'])}")
            else:  # detailed
                print(f"  ~ {path}:")
                print(f"      - {format_value(change['old'])}")
                print(f"      + {format_value(change['new'])}")
    
    if not has_changes:
        print("\n[NO CHANGES]")


def count_changes(diff_result: Dict[str, Dict]) -> Dict[str, int]:
    """
    Count number of changes.
    
    Args:
        diff_result: Output from diff_json()
        
    Returns:
        {'added': count, 'removed': count, 'modified': count, 'total': count}
    """
    counts = {
        'added': len(diff_result.get('added', {})),
        'removed': len(diff_result.get('removed', {})),
        'modified': len(diff_result.get('modified', {}))
    }
    counts['total'] = sum(counts.values())
    return counts


# ===============================================================================
# Directory Diff
# ===============================================================================

def diff_directories(
    old_dir: Path,
    new_dir: Path,
    pattern: str = "*"
) -> Dict[str, List[Path]]:
    """
    Show differences between two directories.
    
    Args:
        old_dir: Original directory
        new_dir: New directory
        pattern: File pattern to match
        
    Returns:
        {
            'added': [files...],
            'removed': [files...],
            'modified': [files...],
            'unchanged': [files...]
        }
    """
    old_files = {f.relative_to(old_dir): f for f in old_dir.rglob(pattern) if f.is_file()}
    new_files = {f.relative_to(new_dir): f for f in new_dir.rglob(pattern) if f.is_file()}
    
    old_paths = set(old_files.keys())
    new_paths = set(new_files.keys())
    
    added = sorted(new_paths - old_paths)
    removed = sorted(old_paths - new_paths)
    
    # Check modified (common files with different content)
    common = old_paths & new_paths
    modified = []
    unchanged = []
    
    for path in sorted(common):
        old_file = old_files[path]
        new_file = new_files[path]
        
        # Compare file sizes first (quick check)
        if old_file.stat().st_size != new_file.stat().st_size:
            modified.append(path)
        else:
            # Compare content
            try:
                with open(old_file, 'rb') as f1, open(new_file, 'rb') as f2:
                    if f1.read() != f2.read():
                        modified.append(path)
                    else:
                        unchanged.append(path)
            except:
                # Can't read, assume modified
                modified.append(path)
    
    return {
        'added': [new_dir / p for p in added],
        'removed': [old_dir / p for p in removed],
        'modified': [new_dir / p for p in modified],
        'unchanged': [new_dir / p for p in unchanged]
    }


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "diff_files",
    "diff_json",
    "show_diff",
    "count_changes",
    "diff_directories"
]
