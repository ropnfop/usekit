# Path: usekit.classes.navi.base.load.sub.nbl_set_sub.py
# -----------------------------------------------------------------------------------------------
#  Set Operation Sub-Procedures
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
import shutil


# ===============================================================================
# Cache Operations
# ===============================================================================

def proc_set_cache(p: dict) -> Any:
    """Set data to runtime cache."""
    from usekit.classes.common.utils.helper_data_cache import (
        set_data_cache, 
        get_data_cache
    )
    
    if not p["name"]:
        p["name"] = p["loc"]
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Auto cache key: {p['loc']}")
    
    if p["data"] is None:
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Set cache: no data provided")
        return None
    
    if p.get("keydata") is not None:
        from usekit.classes.common.utils.helper_keypath import set_key_path
        
        existing = get_data_cache(p["fmt"], p["loc"], p["name"], default={})
        
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Updating keydata: {p['keydata']}")
        
        success = set_key_path(
            existing,
            p["keydata"],
            p["data"],
            create_missing=p.get("create_missing", True),
            recursive=p.get("recursive", False)
        )
        
        if not success:
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Failed to set keydata: {p['keydata']}")
            return None
        
        result = set_data_cache(p["fmt"], p["loc"], p["name"], existing)
        
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Cache updated: {p['name']} (keydata: {p['keydata']})")
        
        return result
    
    result = set_data_cache(p["fmt"], p["loc"], p["name"], p["data"])
    
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Cache set: {p['name']} ({type(p['data']).__name__})")
    
    return result


# ===============================================================================
# Path Operations
# ===============================================================================

def proc_set_path(p: dict) -> Path:
    """Set runtime path configuration (temporary)."""
    from usekit.classes.common.utils.helper_path import get_smart_path
    from usekit.classes.common.utils.helper_path_cache import (
        set_path_cache,
        get_path_cache
    )
    
    if not p.get("dir_path"):
        raise ValueError("[SET_PATH] path parameter is required for dir_path='path'")
    
    new_path = Path(p["dir_path"])
    if not new_path.is_absolute():
        from usekit.classes.core.env.loader_base_path import BASE_PATH
        new_path = (Path(BASE_PATH) / new_path).resolve()
    
    if p.get("cp") == "auto":
        old_path = get_path_cache(p["fmt"], p["loc"])
        if not old_path:
            old_path = get_smart_path(
                fmt=p["fmt"],
                mod=p["mod"],
                filename=None,
                loc=p["loc"],
                user_dir=p.get("dir_path"),
                cus=p.get("cus", False),
                ensure_ext=False
            )
        
        if old_path.exists() and old_path.is_dir():
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Copying from {old_path} to {new_path}")
            
            if new_path.exists():
                print(f"[WARNING] Target path already exists: {new_path}")
                print("[WARNING] Skipping copy. Set cp=None to overwrite manually.")
            else:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(old_path, new_path)
                
                if p["debug"]:
                    count = len(list(new_path.rglob('*')))
                    print(f"[{p['fmt'].upper()}] Copy complete: {count} items")
        else:
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Old path not found: {old_path}")
                print(f"[{p['fmt'].upper()}] Creating new path without copying")
    
    if not new_path.exists():
        new_path.mkdir(parents=True, exist_ok=True)
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Created directory: {new_path}")
    
    set_path_cache(p["fmt"], p["loc"], new_path)
    
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Runtime path set: {p['fmt']}.{p['loc']} → {new_path}")
    
    return new_path


# ===============================================================================
# System Operations
# ===============================================================================

def proc_set_sys(p: dict) -> Path:
    """
    Set system path configuration (permanent).
    
    Features:
    - Modifies sys_const.yaml permanently
    - Format-aware path resolution using resolve_format_section
    - Auto-backup to usekit/sys/sys_yaml/backup/
    - Auto-sync with cp="auto"
    - Safe rollback on failure

    Compatible with:
    - Legacy unified DATA_PATH section
    - New per-format sections (JSON_PATH, YAML_PATH, TXT_PATH, ...)
    """
    from usekit.classes.core.env.loader_base_path import BASE_PATH
    from usekit.classes.common.utils.helper_const import (
        get_const,
        get_sys_path,
        get_sys_const_path,
        clear_sys_const_cache,
        resolve_format_section,
    )
    from usekit.classes.common.utils.helper_path_cache import set_path_cache
    from usekit.classes.common.fileops.helper_backup import (
        backup_file,
        backup_directory,
    )

    if not p.get("dir_path"):
        raise ValueError("[SET_SYS] name parameter required (e.g., 'json_new', 'backup')")

    # [1] Get sys_const.yaml path using helper_const
    config_path = get_sys_const_path()

    if not config_path.exists():
        raise FileNotFoundError(f"[SET_SYS] sys_const.yaml not found: {config_path}")

    # [2] Setup backup directory: usekit/sys/sys_yaml/backup/
    sys_yaml_dir = get_sys_path("yaml")
    backup_dir = sys_yaml_dir / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # [3] Backup sys_const.yaml
    latest_backup, dated_backup = backup_file(
        config_path,
        create_latest=True,
        debug=p.get("debug"),
    )

    if not latest_backup or not dated_backup:
        raise RuntimeError("[SET_SYS] Failed to backup sys_const.yaml")

    # Move backups to backup directory
    import shutil

    for bak in [latest_backup, dated_backup]:
        if bak.exists() and bak.parent != backup_dir:
            target = backup_dir / bak.name
            shutil.move(str(bak), str(target))
            if bak == latest_backup:
                latest_backup = target
            else:
                dated_backup = target

    if p.get("debug"):
        print(f"[{p['fmt'].upper()}] Backups in: {backup_dir.relative_to(BASE_PATH)}")
        print(f"  - {latest_backup.name}")
        print(f"  - {dated_backup.name}")

    # [4] Load config
    import yaml

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"[SET_SYS] Failed to load sys_const.yaml: {e}")

    # [5] Get section from format using helper_const
    try:
        section = resolve_format_section(p["fmt"])
    except ValueError:
        raise ValueError(f"[SET_SYS] Unknown format: {p['fmt']}")

    if p.get("debug"):
        print(f"[{p['fmt'].upper()}] Section: {section}")

    # [6] Resolve YAML key from loc/fmt
    #
    #   공통 규칙:
    #   - loc 가 섹션 키로 직접 존재하면 그대로 사용 (root, sql, pyp, data 등)
    #   - loc 이 'base' / 'sub' 이면:
    #         base → fmt         (예: json  → JSON_PATH.json)
    #         sub  → fmt + '_sub' (예: json → JSON_PATH.json_sub)
    #
    #   섹션 이름(DATA_PATH, JSON_PATH, ...)에는 의존하지 않고,
    #   섹션 안에 fmt / fmt_sub 키만 있으면 동작하도록 일반화.
    loc_key = p["loc"]
    section_cfg = config.get(section, {}) or {}
    yaml_key: Optional[str] = None

    # 1) loc 이름이 그대로 섹션 안에 있을 때 (root, sql, pyp, data 등)
    if loc_key in section_cfg:
        yaml_key = loc_key

    # 2) base / sub → fmt 기반 키로 매핑
    elif loc_key in ("base", "sub"):
        fmt = p["fmt"]
        if loc_key == "base":
            candidate = fmt
        else:  # loc == "sub"
            candidate = f"{fmt}_sub"

        if candidate in section_cfg:
            yaml_key = candidate
        else:
            raise KeyError(
                f"[SET_SYS] {section}.{loc_key} mapped to '{candidate}', "
                f"but {section}.{candidate} not found in sys_const.yaml"
            )

    # 3) 그 외는 잘못된 loc
    else:
        raise KeyError(f"[SET_SYS] {section}.{loc_key} not found in sys_const.yaml")

    try:
        old_loc_name = section_cfg[yaml_key]
    except KeyError:
        # 이 케이스는 위에서 거의 필터링되지만 안전망
        raise KeyError(f"[SET_SYS] {section}.{yaml_key} not found in sys_const.yaml")

    new_loc_name = p["dir_path"]

    # Build absolute paths
    root = config[section]["root"]
    from pathlib import Path

    base = Path(BASE_PATH)

    old_path = (base / root / old_loc_name).resolve()
    new_path = (base / root / new_loc_name).resolve()

    if p.get("debug"):
        print(f"\n[{p['fmt'].upper()}] Path change:")
        print(f"  Section: {section}")
        print(f"  Root: {root}")
        print(f"  Loc: {loc_key} (yaml_key={yaml_key})")
        print(f"  Old: {old_loc_name}")
        print(f"       → {old_path.relative_to(base)}")
        print(f"  New: {new_loc_name}")
        print(f"       → {new_path.relative_to(base)}")

    # [7] Backup old directory
    dir_backup = None
    if p.get("backup_dir", True) and old_path.exists():
        dir_backup = backup_directory(old_path, debug=p.get("debug"))

        if dir_backup and dir_backup.parent != backup_dir:
            target = backup_dir / dir_backup.name
            shutil.move(str(dir_backup), str(target))
            dir_backup = target

            if p.get("debug"):
                print(f"[{p['fmt'].upper()}] Dir backup: {dir_backup.name}")

    # [8] Sync old → new
    if p.get("cp") == "auto" and old_path.exists():
        if new_path.exists():
            print(f"\n[WARNING] Target exists: {new_path.relative_to(base)}")
            print("[WARNING] Skipping sync")
        else:
            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(old_path, new_path)

                if p.get("debug"):
                    count = len(list(new_path.rglob("*")))
                    print(f"\n[{p['fmt'].upper()}] Synced: {count} items")
                    print(f"  {old_path.relative_to(base)}")
                    print(f"  → {new_path.relative_to(base)}")

            except Exception as e:
                if new_path.exists():
                    shutil.rmtree(new_path)
                raise RuntimeError(f"[SET_SYS] Sync failed: {e}")

    # [9] Create new directory
    if not new_path.exists():
        new_path.mkdir(parents=True, exist_ok=True)
        if p.get("debug"):
            print(f"\n[{p['fmt'].upper()}] Created: {new_path.relative_to(base)}")

    # [10] Update sys_const.yaml (using helper_const_line to preserve comments/format)
    try:
        from usekit.classes.common.utils.helper_const_line import load_sys_const_lines
        
        # Load with line-level precision
        lines, index = load_sys_const_lines(config_path)
        
        # Build full key: SECTION.yaml_key
        full_key = f"{section}.{yaml_key}"
        
        if full_key not in index:
            raise KeyError(f"[SET_SYS] Key not found in index: {full_key}")
        
        # Get line info
        line_info = index[full_key]
        line_no = line_info["line_no"]
        old_value = line_info["value_str"]
        
        # Auto-detect quote style from original value
        has_quotes = old_value.startswith('"') and old_value.endswith('"')
        
        if p.get("debug"):
            print(f"\n[{p['fmt'].upper()}] Updating line {line_no}:")
            print(f"  Key: {full_key}")
            print(f"  Old value: {old_value}")
            print(f"  New value: {new_loc_name}")
            print(f"  Quote style: {'preserved' if has_quotes else 'none'}")
        
        # Build new value with same quote style as original
        if has_quotes:
            # Strip quotes from old_value for clean replacement
            old_value_clean = old_value.strip('"')
            new_value_formatted = f'"{new_loc_name}"'
        else:
            old_value_clean = old_value
            new_value_formatted = new_loc_name
        
        # Replace value in original line (preserves comments/indentation/quotes)
        old_line = lines[line_no - 1]
        new_line = old_line.replace(old_value, new_value_formatted, 1)
        lines[line_no - 1] = new_line
        
        # Write back to file
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # Clear both caches
        clear_sys_const_cache()
        load_sys_const_lines.cache_clear()

        if p.get("debug"):
            print(f"[{p['fmt'].upper()}] Updated sys_const.yaml (format preserved):")
            print(f"  {section}.{yaml_key} = {new_value_formatted}")

    except Exception as e:
        print(f"\n[ERROR] Failed to update sys_const.yaml: {e}")
        print("[RECOVERY] Restoring from backup...")

        try:
            shutil.copy2(latest_backup, config_path)
            clear_sys_const_cache()
            print("[RECOVERY] Restored")
        except Exception as restore_err:
            print(f"[RECOVERY] Failed: {restore_err}")
            print(f"[RECOVERY] Manual restore: cp {latest_backup} {config_path}")

        raise RuntimeError(f"[SET_SYS] Failed to update sys_const.yaml: {e}")

    # [11] Update runtime cache
    set_path_cache(p["fmt"], p["loc"], new_path)

    # [12] Success summary
    if p.get("debug"):
        print(f"\n{'=' * 60}")
        print(f"[{p['fmt'].upper()}] System path changed successfully!")
        print(f"{'=' * 60}")
        print(f"Format: {p['fmt']}")
        print(f"Location (loc): {loc_key}")
        print(f"YAML key: {yaml_key}")
        print(f"Section: {section}")
        print(f"Old: {old_loc_name}")
        print(f"New: {new_loc_name}")
        print(f"\nBackups: {backup_dir.relative_to(base)}/")
        print(f"  - {latest_backup.name}")
        print(f"  - {dated_backup.name}")
        if dir_backup:
            print(f"  - {dir_backup.name}")
        print(f"\nRestore: cp {latest_backup} {config_path}")
        print(f"{'=' * 60}\n")

    return new_path

# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "proc_set_cache",
    "proc_set_path",
    "proc_set_sys"
]