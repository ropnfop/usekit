# Path: usekit.classes.common.fileops.helper_backup.py
# -----------------------------------------------------------------------------------------------
#  Backup Utilities
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta
import shutil


# ===============================================================================
# Backup Name Generation
# ===============================================================================

def generate_backup_name(
    target: Path,
    prefix: str = "",
    date_format: str = "%Y%m%d"
) -> Path:
    """Generate backup filename with date + auto-increment sequence."""
    today = datetime.now().strftime(date_format)
    
    if prefix:
        pattern = f"{prefix}.bak.{today}.*"
    else:
        pattern = f"{target.name}.bak.{today}.*"
    
    existing = sorted(target.parent.glob(pattern))
    
    if not existing:
        seq = 1
    else:
        last = existing[-1]
        try:
            last_seq = int(last.suffix[1:])
            seq = last_seq + 1
        except (ValueError, IndexError):
            seq = 1
    
    seq_str = f"{seq:03d}"
    
    if prefix:
        backup_name = f"{prefix}.bak.{today}.{seq_str}"
    else:
        backup_name = f"{target.name}.bak.{today}.{seq_str}"
    
    return target.parent / backup_name


# ===============================================================================
# File Backup
# ===============================================================================

def backup_file(
    file_path: Path,
    create_latest: bool = True,
    prefix: str = "",
    debug: bool = False
) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Backup a file with latest + dated versions.
    
    Creates:
    1. {file}.bak (latest, always overwritten)
    2. {file}.bak.YYYYMMDD.NNN (dated with sequence)
    """
    if not file_path.exists():
        if debug:
            print(f"[BACKUP] File not found: {file_path}")
        return None, None
    
    if not file_path.is_file():
        if debug:
            print(f"[BACKUP] Not a file: {file_path}")
        return None, None
    
    try:
        dated = generate_backup_name(file_path, prefix=prefix)
        shutil.copy2(file_path, dated)
        
        latest = None
        if create_latest:
            latest = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, latest)
        
        if debug:
            size = file_path.stat().st_size
            print(f"[BACKUP] File backed up: {file_path.name} ({size:,}B)")
            if latest:
                print(f"  → {latest.name}")
            print(f"  → {dated.name}")
        
        return latest, dated
    
    except Exception as e:
        if debug:
            print(f"[BACKUP] Failed to backup file: {e}")
        return None, None


# ===============================================================================
# Directory Backup
# ===============================================================================

def backup_directory(
    dir_path: Path,
    create_latest: bool = False,
    prefix: str = "",
    debug: bool = False
) -> Optional[Path]:
    """
    Backup a directory with date + auto-increment.
    
    Creates: {dir}.bak.YYYYMMDD.NNN
    """
    if not dir_path.exists():
        if debug:
            print(f"[BACKUP] Directory not found: {dir_path}")
        return None
    
    if not dir_path.is_dir():
        if debug:
            print(f"[BACKUP] Not a directory: {dir_path}")
        return None
    
    try:
        dated = generate_backup_name(dir_path, prefix=prefix)
        
        if dated.exists():
            shutil.rmtree(dated)
        
        shutil.copytree(dir_path, dated)
        
        if debug:
            count = len(list(dated.rglob('*')))
            total_size = sum(f.stat().st_size for f in dated.rglob('*') if f.is_file())
            print(f"[BACKUP] Directory backed up: {dir_path.name}")
            print(f"  → {dated.name}")
            print(f"  ({count} items, {total_size:,}B)")
        
        return dated
    
    except Exception as e:
        if debug:
            print(f"[BACKUP] Failed to backup directory: {e}")
        return None


# ===============================================================================
# Cleanup
# ===============================================================================

def cleanup_old_backups(
    directory: Path,
    pattern: str = "*.bak.*",
    days: int = 30,
    keep_latest: int = 3,
    debug: bool = False
) -> Tuple[int, int]:
    """
    Clean up old backup files.
    
    Strategy:
    - Delete backups older than N days
    - Always keep N latest backups per day
    """
    from collections import defaultdict
    
    cutoff = datetime.now() - timedelta(days=days)
    backups = sorted(directory.glob(pattern))
    
    if not backups:
        if debug:
            print("[CLEANUP] No backups found")
        return 0, 0
    
    by_date = defaultdict(list)
    
    for backup in backups:
        try:
            parts = backup.name.split('.bak.')
            if len(parts) >= 2:
                date_part = parts[1].split('.')[0]
                by_date[date_part].append(backup)
        except (IndexError, ValueError):
            if debug:
                print(f"[CLEANUP] Skipping invalid backup name: {backup.name}")
    
    deleted = 0
    kept = 0
    
    for date_str, date_backups in by_date.items():
        try:
            date = datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            if debug:
                print(f"[CLEANUP] Invalid date format: {date_str}")
            continue
        
        sorted_backups = sorted(date_backups, reverse=True)
        
        to_keep = sorted_backups[:keep_latest]
        to_delete = sorted_backups[keep_latest:]
        
        if date < cutoff:
            for backup in to_delete:
                try:
                    if backup.is_file():
                        backup.unlink()
                    elif backup.is_dir():
                        shutil.rmtree(backup)
                    
                    if debug:
                        print(f"[CLEANUP] Deleted: {backup.name}")
                    deleted += 1
                
                except Exception as e:
                    if debug:
                        print(f"[CLEANUP] Failed to delete {backup.name}: {e}")
        else:
            to_keep = sorted_backups
        
        kept += len(to_keep)
    
    if debug:
        print(f"\n[CLEANUP] Summary: Deleted {deleted}, Kept {kept}")
    
    return deleted, kept


# ===============================================================================
# List Backups
# ===============================================================================

def list_backups(
    directory: Path,
    pattern: str = "*.bak.*",
    show_details: bool = True
) -> List[Dict]:
    """List all backups with details."""
    backups = sorted(directory.glob(pattern))
    results = []
    
    for backup in backups:
        try:
            stat = backup.stat()
            
            info = {
                'path': backup,
                'name': backup.name,
                'size': stat.st_size,
                'mtime': datetime.fromtimestamp(stat.st_mtime),
                'is_dir': backup.is_dir()
            }
            
            if backup.is_dir():
                items = list(backup.rglob('*'))
                info['item_count'] = len(items)
                info['total_size'] = sum(f.stat().st_size for f in items if f.is_file())
            
            results.append(info)
            
            if show_details:
                if backup.is_dir():
                    size_str = f"{info['item_count']} items"
                else:
                    size_str = f"{info['size']:,}B"
                
                print(f"{backup.name:50s} {size_str:>15s}  {info['mtime']:%Y-%m-%d %H:%M:%S}")
        
        except Exception as e:
            if show_details:
                print(f"[ERROR] Failed to process {backup.name}: {e}")
    
    return results


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "generate_backup_name",
    "backup_file",
    "backup_directory",
    "cleanup_old_backups",
    "list_backups"
]