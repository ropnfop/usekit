# Path: usekit.classes.navi.base.load.ops.nbl_set.py
# -----------------------------------------------------------------------------------------------
#  Set Operation - Cache/Path/System Configuration
#  Created by: THE Little Prince × ROP × FOP
#  
#  Philosophy:
#  - op="cache" (default): Runtime cache management (session-based)
#  - op="path": Runtime path configuration (session-based)
#  - op="sys": System path configuration (permanent, modifies const_sys.yaml)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any

from usekit.infra.navi_signature import params_for_set, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise

# Import sub-procedures
from usekit.classes.navi.base.load.sub.nbl_set_sub import (
    proc_set_cache,
    proc_set_path,
    proc_set_sys
)


# ===============================================================================
# Main Set Operation
# ===============================================================================

@log_and_raise
def set_operation(**kwargs) -> Any:
    """
    Set operation - Cache/Path/System configuration.
    
    Philosophy:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Set = Configuration & Storage
    - op="cache": Store data in runtime memory (fast, temporary)
    - op="path": Change runtime path (session-based, temporary)
    - op="sys": Change system path (permanent, modifies const_sys.yaml)
    
    Operations:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    op="cache" (default):
    - Stores data in runtime memory
    - Fast access (no disk I/O)
    - Session-based (cleared on restart)
    - Auto-naming: Uses loc as cache key if name not provided
    - Partial update: Supports keydata for nested field updates
    
    op="path":
    - Changes runtime path temporarily
    - Session-based (reverts on restart)
    - Does not modify const_sys.yaml
    - Auto-copy: If cp="auto", copies old path contents
    
    op="sys":
    - Changes system path permanently
    - Modifies const_sys.yaml (survives restart)
    - Auto-backup: Creates .bak files with date + sequence
    - Auto-sync: If cp="auto", syncs old → new directory
    - Safe: Auto-rollback on failure
    
    Args:
        **kwargs: Common Navigation parameters
        
        # Core
        fmt: File format (json/yaml/txt/csv/any)
        name: Cache key or location name
        loc: Location (base/sub/dir/now/tmp/cache)
        
        # Data (for op="cache")
        data: Data to store in cache
        keydata: Field path for partial update (e.g., "user/email")
        create_missing: Create missing keys in keydata path
        recursive: Recursive keydata navigation
        
        # Path (for op="path" or op="sys")
        path: New path (for op="path")
        name: New location name (for op="sys", e.g., "1233", "backup")
        
        # Options
        op: Operation type ("cache", "path", "sys")
        cp: Copy mode ("auto" to copy contents)
        backup_dir: Backup directory before changing (default: True)
        
        debug: Debug mode
    
    Returns:
        op="cache": Cached data
        op="path": New runtime path
        op="sys": New system path
    
    Examples:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # [1] Cache (default)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Store data
        >>> set_operation(fmt="json", loc="base", data={"key": "value"})
        {'key': 'value'}
        
        >>> u.sjb({"key": "value"})
        {'key': 'value'}
        
        # Auto-naming (uses loc as cache key)
        >>> u.sjb(data)  # cache key: "json.base.base"
        
        # Explicit naming
        >>> u.sjb(data, name="config")  # cache key: "json.base.config"
        
        # Partial update via keydata
        >>> u.sjb("new@email.com", name="config", keydata="user/email")
        # Updates only config.user.email field
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # [2] Path (runtime, temporary)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Change runtime path
        >>> set_operation(
        ...     fmt="json",
        ...     loc="base",
        ...     path="/custom/json",
        ...     op="path"
        ... )
        PosixPath('/custom/json')
        
        >>> u.sjb(path="/custom/json", op="path")
        # After this, u.rjb() reads from /custom/json
        # Reverts after restart
        
        # With auto-copy
        >>> u.sjb(path="/backup/json", op="path", cp="auto")
        # Copies old path contents to new path
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # [3] Sys (system, permanent)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Change system path permanently
        >>> set_operation(
        ...     fmt="json",
        ...     loc="base",
        ...     name="project_v2",
        ...     op="sys",
        ...     debug=True
        ... )
        
        >>> u.sjb("project_v2", op="sys", debug=True)
        # [BACKUP] ✓ YAML backed up:
        #   → const_sys.yaml.bak
        #   → const_sys.yaml.bak.20241127.001
        # [BACKUP] ✓ Directory backed up:
        #   json_main → json_main.bak.20241127.001
        # [JSON] ✓ Updated const_sys.yaml:
        #   path.json.base = 'project_v2'
        # ✓ System path changed successfully!
        
        # With auto-sync
        >>> u.sjb("backup", op="sys", cp="auto")
        # Copies old directory → new directory
        # Updates const_sys.yaml
        # Creates backups with date + sequence
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # [4] Practical workflows
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Quick cache
        >>> u.sjb(expensive_result)
        >>> later = u.gjb()  # Fast retrieval
        
        # Temporary experiment
        >>> u.sjb(path="/experiment", op="path")
        >>> # ... work ...
        >>> # Restart → back to normal
        
        # Permanent project switch
        >>> u.sjb("project_2024", op="sys", cp="auto")
        >>> # Restart → still uses project_2024
        
        # Safe backup before changes
        >>> u.sjb("backup_20241127", op="sys", cp="auto")
        >>> # All data copied to backup folder
        >>> # YAML + directory backed up with date + sequence
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Extract Parameters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    p = params_for_set(**kwargs)

    # op=path/sys system_default
    if p.get("op") in ("path", "sys") and p.get("data") is None:
        p["data"] = "system_default"
        
    if p.get("op") in ("path", "sys") and p.get("name") is None:
        p["name"] = "system_default"
        
    # Warn about future features
    warn_future_features(p)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Route to Sub-Procedure
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if p["op"] == "sys":
        # System path (permanent)
        return proc_set_sys(p)
    
    elif p["op"] == "path":
        # Runtime path (temporary)
        return proc_set_path(p)
    
    else:
        # Cache (default)
        return proc_set_cache(p)


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["set_operation"]