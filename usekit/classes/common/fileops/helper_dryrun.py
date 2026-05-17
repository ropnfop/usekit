# Path: usekit.classes.common.fileops.helper_dryrun.py
# -----------------------------------------------------------------------------------------------
#  Dry-run Utilities - Preview operations before execution
#  Created by: THE Little Prince × ROP × FOP
#  
#  Philosophy:
#  - Preview dangerous operations before execution
#  - Show detailed impact analysis
#  - Get user confirmation for irreversible actions
#  - Prevent accidental data loss
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, List, Dict, Optional, Callable
import sys


# ===============================================================================
# Delete Preview
# ===============================================================================

def preview_delete(
    targets: List[Path],
    show_size: bool = True,
    show_content: bool = False,
    max_items: int = 100
) -> Dict[str, Any]:
    """
    Preview delete operation.
    
    Shows what would be deleted without actually deleting.
    
    Args:
        targets: Files/directories to delete
        show_size: Show file/directory sizes
        show_content: Show directory contents
        max_items: Maximum items to display
        
    Returns:
        {
            'file_count': int,
            'dir_count': int,
            'total_size': int,
            'targets': List[Path]
        }
        
    Examples:
        >>> files = [Path("old1.json"), Path("old2.json")]
        >>> preview_delete(files)
        
        [DRY-RUN] Would delete:
        ========================================
          - old1.json (1024B)
          - old2.json (2048B)
        ========================================
        Total: 2 files, 3072B (0.00MB)
    """
    total_size = 0
    file_count = 0
    dir_count = 0
    item_details = []
    
    # Analyze targets
    for target in targets:
        if not target.exists():
            continue
        
        if target.is_file():
            size = target.stat().st_size
            total_size += size
            file_count += 1
            
            item_details.append({
                'path': target,
                'type': 'file',
                'size': size,
                'items': 1
            })
        
        elif target.is_dir():
            # Count items in directory
            items = list(target.rglob('*'))
            files_in_dir = [f for f in items if f.is_file()]
            dir_size = sum(f.stat().st_size for f in files_in_dir)
            
            total_size += dir_size
            dir_count += 1
            
            item_details.append({
                'path': target,
                'type': 'dir',
                'size': dir_size,
                'items': len(items)
            })
    
    # Display preview
    print("\n[DRY-RUN] Would delete:")
    print("=" * 60)
    
    displayed = 0
    for detail in item_details:
        if displayed >= max_items:
            remaining = len(item_details) - displayed
            print(f"  ... and {remaining} more items")
            break
        
        path = detail['path']
        
        if detail['type'] == 'file':
            if show_size:
                print(f"  - {path.name} ({detail['size']:,}B)")
            else:
                print(f"  - {path.name}")
        
        elif detail['type'] == 'dir':
            if show_size:
                print(f"  - {path.name}/ ({detail['items']} items, {detail['size']:,}B)")
            else:
                print(f"  - {path.name}/ ({detail['items']} items)")
            
            # Show directory contents if requested
            if show_content and displayed < max_items - 1:
                try:
                    contents = sorted(path.iterdir())[:10]
                    for item in contents:
                        print(f"      • {item.name}")
                    if len(list(path.iterdir())) > 10:
                        print(f"      • ... and more")
                except:
                    pass
        
        displayed += 1
    
    print("=" * 60)
    
    # Summary
    total_mb = total_size / (1024 * 1024)
    summary_parts = []
    if file_count > 0:
        summary_parts.append(f"{file_count} file{'s' if file_count != 1 else ''}")
    if dir_count > 0:
        summary_parts.append(f"{dir_count} director{'ies' if dir_count != 1 else 'y'}")
    
    summary = ", ".join(summary_parts) if summary_parts else "0 items"
    print(f"Total: {summary}, {total_size:,}B ({total_mb:.2f}MB)")
    print()
    
    return {
        'file_count': file_count,
        'dir_count': dir_count,
        'total_size': total_size,
        'total_items': file_count + dir_count,
        'targets': targets
    }


# ===============================================================================
# Update Preview
# ===============================================================================

def preview_update(
    old_data: Any,
    new_data: Any,
    format: str = "json",
    show_diff: bool = True
) -> Dict[str, Any]:
    """
    Preview update operation.
    
    Shows what would change before applying update.
    
    Args:
        old_data: Current data
        new_data: New data
        format: Data format ("json", "text")
        show_diff: Show detailed differences
        
    Returns:
        Diff result dict
        
    Examples:
        >>> old = {'user': 'alice', 'age': 25}
        >>> new = {'user': 'alice', 'age': 26}
        >>> preview_update(old, new)
        
        [DRY-RUN] Would update:
        ========================================
        [MODIFIED]
          ~ age:
              old: 25
              new: 26
        ========================================
    """
    from usekit.classes.common.fileops.helper_diff import diff_json, show_diff as display_diff
    
    print("\n[DRY-RUN] Would update:")
    print("=" * 60)
    
    if format == "json" and show_diff:
        diff = diff_json(old_data, new_data)
        display_diff(diff)
        print("=" * 60)
        print()
        return diff
    else:
        print("Old data:", old_data)
        print("New data:", new_data)
        print("=" * 60)
        print()
        return {}


# ===============================================================================
# Write Preview
# ===============================================================================

def preview_write(
    target_path: Path,
    data: Any,
    format: str = "json",
    show_preview: bool = True,
    preview_lines: int = 20
) -> Dict[str, Any]:
    """
    Preview write operation.
    
    Shows what would be written to file.
    
    Args:
        target_path: Target file path
        data: Data to write
        format: Data format
        show_preview: Show data preview
        preview_lines: Number of lines to preview
        
    Returns:
        Preview info dict
    """
    import json
    
    exists = target_path.exists()
    will_overwrite = exists
    
    print("\n[DRY-RUN] Would write:")
    print("=" * 60)
    print(f"Target: {target_path}")
    print(f"Action: {'Overwrite' if will_overwrite else 'Create new'}")
    
    if show_preview:
        print("\nData preview:")
        print("-" * 60)
        
        if format == "json":
            preview_text = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            preview_text = str(data)
        
        lines = preview_text.split('\n')
        for i, line in enumerate(lines[:preview_lines]):
            print(line)
        
        if len(lines) > preview_lines:
            print(f"... ({len(lines) - preview_lines} more lines)")
        
        print("-" * 60)
    
    size_estimate = len(str(data))
    print(f"Estimated size: {size_estimate:,}B")
    print("=" * 60)
    print()
    
    return {
        'target': target_path,
        'exists': exists,
        'will_overwrite': will_overwrite,
        'size_estimate': size_estimate
    }


# ===============================================================================
# Confirmation
# ===============================================================================

def confirm_action(
    message: str = "Continue?",
    default: bool = False,
    skip_confirm: bool = False
) -> bool:
    """
    Ask for user confirmation.
    
    Args:
        message: Confirmation message
        default: Default choice if user just presses Enter
        skip_confirm: Skip confirmation (always return True)
        
    Returns:
        True if user confirms, False otherwise
        
    Examples:
        >>> if confirm_action("Delete these files?"):
        ...     delete_files()
        Delete these files? [y/N]: y
        True
    """
    if skip_confirm:
        return True
    
    # Format choices
    if default:
        choices = "Y/n"
        default_str = "yes"
    else:
        choices = "y/N"
        default_str = "no"
    
    # Show prompt
    prompt = f"\n{message} [{choices}]: "
    
    try:
        response = input(prompt).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n[CANCELLED]")
        return False
    
    # Handle response
    if not response:
        return default
    
    return response in ['y', 'yes']


# ===============================================================================
# Batch Confirmation
# ===============================================================================

def confirm_batch(
    items: List[Any],
    action: str = "process",
    max_display: int = 10
) -> bool:
    """
    Confirm batch operation on multiple items.
    
    Args:
        items: Items to process
        action: Action description
        max_display: Maximum items to display
        
    Returns:
        True if user confirms
    """
    print(f"\n[CONFIRMATION] About to {action} {len(items)} item(s):")
    print("-" * 60)
    
    for i, item in enumerate(items[:max_display]):
        print(f"  {i+1}. {item}")
    
    if len(items) > max_display:
        remaining = len(items) - max_display
        print(f"  ... and {remaining} more")
    
    print("-" * 60)
    
    return confirm_action(f"Proceed to {action} these items?")


# ===============================================================================
# Safe Execute
# ===============================================================================

def safe_execute(
    operation: Callable,
    preview_fn: Optional[Callable] = None,
    confirm_message: str = "Execute this operation?",
    dry_run: bool = False,
    skip_confirm: bool = False,
    **kwargs
) -> Any:
    """
    Safely execute operation with preview and confirmation.
    
    Args:
        operation: Function to execute
        preview_fn: Preview function (called before confirmation)
        confirm_message: Confirmation message
        dry_run: If True, only show preview
        skip_confirm: Skip confirmation
        **kwargs: Arguments for operation
        
    Returns:
        Operation result or None (if cancelled or dry-run)
        
    Examples:
        >>> def delete_files(files):
        ...     for f in files:
        ...         f.unlink()
        
        >>> safe_execute(
        ...     delete_files,
        ...     preview_fn=lambda: preview_delete(files),
        ...     files=files
        ... )
    """
    # Show preview
    if preview_fn:
        preview_fn()
    
    # Dry-run: stop here
    if dry_run:
        print("[DRY-RUN] Operation not executed (dry_run=True)")
        return None
    
    # Get confirmation
    if not skip_confirm:
        if not confirm_action(confirm_message):
            print("[CANCELLED] Operation not executed")
            return None
    
    # Execute operation
    try:
        result = operation(**kwargs)
        print("[SUCCESS] Operation completed")
        return result
    except Exception as e:
        print(f"[ERROR] Operation failed: {e}")
        raise


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "preview_delete",
    "preview_update",
    "preview_write",
    "confirm_action",
    "confirm_batch",
    "safe_execute"
]
