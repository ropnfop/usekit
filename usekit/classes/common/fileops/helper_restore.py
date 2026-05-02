# Path: usekit.classes.common.fileops.helper_restore.py
# -----------------------------------------------------------------------------------------------
#  Restore Utilities
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import shutil

# ===============================================================================
# Restore point
# ===============================================================================

def select_restore_point(
    target: Path,
    restore: Any,
    backup_dir: Optional[Path] = None,
    debug: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Select a restore point using restore selector.

    restore:
        - True        : latest backup
        - int (>=1)   : N-th backup (1-based), using list_restore_points order
        - str         : full backup name or suffix such as '20251201.001'

    Returns:
        Backup info dict from list_restore_points() or None.
    """
    restore_points = list_restore_points(
        target=target,
        backup_dir=backup_dir,
        show_details=False,
    )
    if not restore_points:
        if debug:
            print(f"[RESTORE] No backups for target: {target}")
        return None

    # 1) restore=True → latest (가장 최근)
    if restore is True:
        # list_restore_points 를 최신순/오래된순 중 어느 쪽으로 정렬했는지에 따라
        # 필요하면 [-1] ↔ [0] 조정
        return restore_points[-1]

    # 2) restore=int → N-th (1-based index)
    if isinstance(restore, int):
        idx = restore - 1
        if 0 <= idx < len(restore_points):
            return restore_points[idx]
        if debug:
            print(f"[RESTORE] Invalid restore index: {restore}")
        return None

    # 3) restore=str → full name or suffix
    if isinstance(restore, str):
        # full name match
        for point in restore_points:
            if point["name"] == restore:
                return point

        # suffix match (e.g., '20251201.001')
        for point in restore_points:
            if point["name"].endswith(restore):
                return point

        if debug:
            print(f"[RESTORE] No backup matched restore={restore}")
        return None

    if debug:
        print(f"[RESTORE] Unsupported restore type: {type(restore)}")
    return None

# ===============================================================================
# Restore
# ===============================================================================

def restore_backup(
    backup_path: Path,
    target_path: Optional[Path] = None,
    backup_current: bool = True,
    dry_run: bool = False,
    debug: bool = False
) -> bool:
    """
    Restore from backup.
    
    Args:
        backup_path: Backup file/directory to restore from
        target_path: Target path (auto-detected from backup name if None)
        backup_current: Backup current file before restoring
        dry_run: Preview without executing
        debug: Debug output
    """
    if not backup_path.exists():
        if debug:
            print(f"[RESTORE] Backup not found: {backup_path}")
        return False
    
    if target_path is None:
        parts = backup_path.name.split('.bak.')
        if len(parts) < 2:
            if debug:
                print(f"[RESTORE] Cannot detect target from: {backup_path.name}")
            return False
        
        target_name = parts[0]
        target_path = backup_path.parent / target_name
    
    # Dry-run preview
    if dry_run:
        print("\n[DRY-RUN] Would restore:")
        print("=" * 60)
        print(f"From: {backup_path}")
        print(f"To:   {target_path}")
        print(f"Type: {'Directory' if backup_path.is_dir() else 'File'}")
        
        if backup_path.is_dir():
            items = list(backup_path.rglob('*'))
            file_count = sum(1 for f in items if f.is_file())
            print(f"Items: {len(items)} total, {file_count} files")
        else:
            size = backup_path.stat().st_size
            print(f"Size: {size:,}B")
        
        if target_path.exists():
            print(f"Action: Overwrite existing")
            if backup_current:
                print(f"Current will be backed up to: {target_path.name}.bak.before_restore")
        else:
            print(f"Action: Create new")
        
        print("=" * 60)
        return True
    
    # Backup current if requested
    if backup_current and target_path.exists():
        current_backup = target_path.with_name(
            target_path.name + '.bak.before_restore'
        )
        
        try:
            if target_path.is_dir():
                if current_backup.exists():
                    shutil.rmtree(current_backup)
                shutil.copytree(target_path, current_backup)
            else:
                shutil.copy2(target_path, current_backup)
            
            if debug:
                print(f"[RESTORE] Current backed up: {current_backup.name}")
        except Exception as e:
            if debug:
                print(f"[RESTORE] Warning: Failed to backup current: {e}")
    
    # Execute restore
    try:
        if backup_path.is_dir():
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(backup_path, target_path)
        else:
            shutil.copy2(backup_path, target_path)
        
        if debug:
            print(f"[RESTORE] Restored: {backup_path.name} → {target_path.name}")
        
        return True
    
    except Exception as e:
        if debug:
            print(f"[RESTORE] Failed to restore: {e}")
        return False


# ===============================================================================
# Restore with Diff
# ===============================================================================

def restore_with_diff(
    backup_path: Path,
    target_path: Optional[Path] = None,
    show_diff: bool = True,
    confirm: bool = True,
    backup_current: bool = True,
    debug: bool = False
) -> bool:
    """
    Restore with diff preview and confirmation.
    
    Args:
        backup_path: Backup file to restore from
        target_path: Target path (auto-detected if None)
        show_diff: Show differences before restoring
        confirm: Ask for confirmation
        backup_current: Backup current before restoring
        debug: Debug output
    """
    from usekit.classes.common.fileops.helper_diff import diff_files, diff_json
    import json
    
    if not backup_path.exists():
        if debug:
            print(f"[RESTORE] Backup not found: {backup_path}")
        return False
    
    if target_path is None:
        parts = backup_path.name.split('.bak.')
        if len(parts) < 2:
            if debug:
                print(f"[RESTORE] Cannot detect target from: {backup_path.name}")
            return False
        target_name = parts[0]
        target_path = backup_path.parent / target_name
    
    # Show diff if requested and target exists
    if show_diff and target_path.exists():
        print("\n[DIFF] Changes from current to backup:")
        print("=" * 60)
        
        try:
            if backup_path.suffix in ['.json']:
                with open(target_path) as f:
                    current_data = json.load(f)
                with open(backup_path) as f:
                    backup_data = json.load(f)
                
                from usekit.classes.common.fileops.helper_diff import show_diff as display_diff
                diff = diff_json(current_data, backup_data)
                display_diff(diff)
            else:
                diff_output = diff_files(target_path, backup_path)
                print(diff_output)
        except Exception as e:
            if debug:
                print(f"[DIFF] Could not show diff: {e}")
        
        print("=" * 60)
    
    # Confirm if requested
    if confirm:
        from usekit.classes.common.fileops.helper_dryrun import confirm_action
        if not confirm_action("Proceed with restore?"):
            print("[CANCELLED] Restore cancelled")
            return False
    
    # Execute restore
    return restore_backup(
        backup_path,
        target_path,
        backup_current=backup_current,
        dry_run=False,
        debug=debug
    )


# ===============================================================================
# Restore to Timestamp
# ===============================================================================

def restore_to_timestamp(
    target: Path,
    timestamp: str,
    backup_dir: Optional[Path] = None,
    dry_run: bool = False,
    debug: bool = False
) -> bool:
    """
    Restore file/directory to specific timestamp.
    
    Args:
        target: Target file/directory
        timestamp: Date string (YYYYMMDD format)
        backup_dir: Backup directory (uses parent if None)
        dry_run: Preview without executing
        debug: Debug output
        
    Examples:
        >>> restore_to_timestamp(Path("config.json"), "20241127")
        [RESTORE] Found backup: config.json.bak.20241127.003
    """
    if backup_dir is None:
        backup_dir = target.parent
    
    pattern = f"{target.name}.bak.{timestamp}.*"
    backups = sorted(backup_dir.glob(pattern))
    
    if not backups:
        if debug:
            print(f"[RESTORE] No backups found for {timestamp}")
        return False
    
    latest_backup = backups[-1]
    
    if debug:
        print(f"[RESTORE] Found backup: {latest_backup.name}")
    
    return restore_backup(
        latest_backup,
        target,
        backup_current=True,
        dry_run=dry_run,
        debug=debug
    )


# ===============================================================================
# List Available Restores
# ===============================================================================

def list_restore_points(
    target: Path,
    backup_dir: Optional[Path] = None,
    show_details: bool = True
) -> List[Dict[str, Any]]:
    """
    List available restore points for a file/directory.
    
    Args:
        target: Target file/directory
        backup_dir: Backup directory (uses parent if None)
        show_details: Print details to console
        
    Returns:
        List of backup info dicts
    """
    if backup_dir is None:
        backup_dir = target.parent
    
    pattern = f"{target.name}.bak.*"
    backups = sorted(backup_dir.glob(pattern))
    
    if not backups:
        if show_details:
            print(f"[RESTORE] No backups found for: {target.name}")
        return []
    
    results = []
    
    if show_details:
        print(f"\n[RESTORE] Available restore points for: {target.name}")
        print("=" * 60)
    
    for backup in backups:
        try:
            stat = backup.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            parts = backup.name.split('.bak.')
            timestamp = parts[1].split('.')[0] if len(parts) > 1 else "unknown"
            
            info = {
                'path': backup,
                'name': backup.name,
                'timestamp': timestamp,
                'size': stat.st_size,
                'mtime': mtime,
                'is_dir': backup.is_dir()
            }
            
            results.append(info)
            
            if show_details:
                if backup.is_dir():
                    items = list(backup.rglob('*'))
                    size_str = f"{len(items)} items"
                else:
                    size_str = f"{info['size']:,}B"
                
                print(f"{backup.name:50s} {size_str:>15s}  {mtime:%Y-%m-%d %H:%M:%S}")
        
        except Exception as e:
            if show_details:
                print(f"[ERROR] Failed to process {backup.name}: {e}")
    
    if show_details:
        print("=" * 60)
        print(f"Total: {len(results)} restore point(s)")
        print()
    
    return results


# ===============================================================================
# Smart Restore (Interactive)
# ===============================================================================

def smart_restore(
    target: Path,
    backup_dir: Optional[Path] = None,
    auto_select: bool = False,
    show_diff: bool = True,
    debug: bool = False
) -> bool:
    """
    Interactive restore with backup selection.
    
    Args:
        target: Target file/directory
        backup_dir: Backup directory (uses parent if None)
        auto_select: Auto-select latest backup
        show_diff: Show diff preview
        debug: Debug output
    """
    restore_points = list_restore_points(target, backup_dir, show_details=True)
    
    if not restore_points:
        return False
    
    if auto_select:
        selected = restore_points[-1]
        print(f"\n[AUTO] Selected latest: {selected['name']}")
    else:
        print("\nSelect restore point:")
        for i, point in enumerate(restore_points, 1):
            print(f"  {i}. {point['name']}")
        
        try:
            choice = input("\nEnter number (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                print("[CANCELLED]")
                return False
            
            idx = int(choice) - 1
            if 0 <= idx < len(restore_points):
                selected = restore_points[idx]
            else:
                print("[ERROR] Invalid selection")
                return False
        except (ValueError, KeyboardInterrupt):
            print("\n[CANCELLED]")
            return False
    
    return restore_with_diff(
        selected['path'],
        target,
        show_diff=show_diff,
        confirm=True,
        backup_current=True,
        debug=debug
    )


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "restore_backup",
    "restore_with_diff",
    "restore_to_timestamp",
    "list_restore_points",
    "smart_restore"
]