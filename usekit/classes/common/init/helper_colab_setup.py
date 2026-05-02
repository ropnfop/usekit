# Path: usekit/classes/common/init/helper_colab_setup.py
# ----------------------------------------------------------------------------------------------- 
# Created by: The Little Prince × ROP × FOP
# Version: v1.0-colab-init (2025-01-18)
# — memory is emotion, speed is essence —
# ----------------------------------------------------------------------------------------------- 
"""
Google Colab Environment Setup Helper

Provides user-friendly initialization for Google Colab with Drive mounting.
Minimal setup with .env and sys_const.yaml for user editing.

IMPORTANT: Following Termux pattern
- On import: Warning message only (no input())
- On use.colab(): Interactive setup with user confirmation
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Optional, Dict


def is_colab() -> bool:
    """Check if running in Google Colab environment"""
    try:
        import google.colab  # noqa
        return True
    except ImportError:
        return False


def check_drive_mount() -> bool:
    """
    Check if Google Drive is mounted
    
    Returns:
        bool: True if /content/drive/MyDrive is accessible
    """
    try:
        drive_path = Path("/content/drive/MyDrive")
        return drive_path.exists() and os.access(drive_path, os.W_OK)
    except Exception:
        return False


def get_drive_setup_path() -> Path:
    """Get the target setup path in Google Drive"""
    return Path("/content/drive/MyDrive/PROJECTS/pj01/usekit")


def get_volatile_setup_path() -> Path:
    """Get the volatile setup path in /content"""
    return Path("/content/usekit")


def check_setup_status(verbose: bool = False) -> Dict[str, any]:
    """
    Get detailed Colab setup status
    
    Args:
        verbose: Print status information
    
    Returns:
        dict: Status information
    """
    drive_mounted = check_drive_mount()
    drive_path = get_drive_setup_path()
    volatile_path = get_volatile_setup_path()
    
    status = {
        'is_colab': is_colab(),
        'drive_mounted': drive_mounted,
        'drive_setup_exists': drive_path.exists() if drive_mounted else False,
        'volatile_setup_exists': volatile_path.exists(),
        'setup_location': None,
        'ready': False
    }
    
    # Determine setup location
    if status['drive_setup_exists']:
        status['setup_location'] = str(drive_path)
        status['ready'] = True
    elif status['volatile_setup_exists']:
        status['setup_location'] = str(volatile_path)
        status['ready'] = True
    
    if verbose:
        print("\n" + "="*60)
        print("[USEKIT] Colab Environment Status")
        print("="*60)
        print(f"  Colab Environment:  {'✓' if status['is_colab'] else '✗'}")
        print(f"  Drive Mounted:      {'✓' if status['drive_mounted'] else '✗'}")
        print(f"  Drive Setup:        {'✓' if status['drive_setup_exists'] else '✗'}")
        print(f"  Volatile Setup:     {'✓' if status['volatile_setup_exists'] else '✗'}")
        
        if status['setup_location']:
            print(f"  Setup Location:     {status['setup_location']}")
        
        print(f"  Overall Status:     {'READY ✓' if status['ready'] else 'NOT READY ✗'}")
        print("="*60 + "\n")
    
    return status


def _copy_setup_files(target_path: Path, verbose: bool = True) -> bool:
    """
    Copy minimal setup files (.env.example, sys_const.yaml) to target location
    
    Args:
        target_path: Target directory for setup files
        verbose: Print progress messages
    
    Returns:
        bool: True if successful
    """
    try:
        # Create target directory
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Find source files from installed package
        # This file is at: usekit/classes/common/init/helper_colab_setup.py
        # Package root is 4 levels up
        current = Path(__file__).resolve()
        package_root = current.parents[3]  # Go up to 'usekit' directory
        
        # Source files
        env_example = package_root / ".env.example"
        sys_const = package_root / "sys" / "sys_yaml" / "sys_const.yaml"
        
        # Target files
        target_env = target_path / ".env"
        target_sys = target_path / "sys_const.yaml"
        
        # Copy .env.example -> .env (if not exists)
        if env_example.exists():
            if not target_env.exists():
                shutil.copy2(env_example, target_env)
                if verbose:
                    print(f"[OK] Created: {target_env}")
            else:
                if verbose:
                    print(f"[SKIP] Already exists: {target_env}")
        else:
            # Create minimal .env if source not found
            if not target_env.exists():
                minimal_env = f"""# USEKIT Configuration
# Auto-generated for Colab environment

ENV_BASE_PATH={target_path.parent}
USEKIT_PATH={target_path}
"""
                target_env.write_text(minimal_env)
                if verbose:
                    print(f"[OK] Created minimal: {target_env}")
        
        # Copy sys_const.yaml (if not exists)
        if sys_const.exists():
            if not target_sys.exists():
                shutil.copy2(sys_const, target_sys)
                if verbose:
                    print(f"[OK] Created: {target_sys}")
            else:
                if verbose:
                    print(f"[SKIP] Already exists: {target_sys}")
        else:
            if verbose:
                print(f"[WARN] Source not found: {sys_const}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to copy setup files: {e}")
        return False


def setup_colab_drive(force: bool = False, verbose: bool = True, interactive: bool = True) -> bool:
    """
    Setup USEKIT in Google Drive with user confirmation
    
    Creates minimal setup at /content/drive/MyDrive/PROJECTS/pj01/usekit/
    with .env and sys_const.yaml for user editing.
    
    Args:
        force: Reinstall even if files exist
        verbose: Print detailed information
        interactive: Ask for user confirmation
    
    Returns:
        bool: True if setup succeeded
    
    Examples:
        >>> from usekit import use
        >>> use.colab()
        [USEKIT] Setting up Google Drive integration...
        ✓ Setup complete!
    """
    # Check if in Colab
    if not is_colab():
        if verbose:
            print("[USEKIT] Not running in Google Colab environment")
        return False
    
    # Check Drive mount
    if not check_drive_mount():
        if verbose:
            print()
            print("="*60)
            print("[USEKIT] Google Drive Not Mounted")
            print("="*60)
            print()
            print("Please mount Google Drive first:")
            print()
            print("  from google.colab import drive")
            print("  drive.mount('/content/drive')")
            print()
            print("Then run: use.colab()")
            print("="*60 + "\n")
        return False
    
    # Get setup path
    setup_path = get_drive_setup_path()
    
    # Check if already exists
    if setup_path.exists() and not force:
        if verbose:
            print(f"[USEKIT] ✓ Already installed at: {setup_path}")
            print("[USEKIT] Use force=True to reinstall")
        
        # Set environment variable
        os.environ["ENV_BASE_PATH"] = str(setup_path.parent)
        return True
    
    # Show explanation if verbose
    if verbose:
        print("\n" + "="*60)
        print("[USEKIT] Google Drive Setup")
        print("="*60)
        print()
        print("USEKIT will create:")
        print(f"  Location: {setup_path}")
        print()
        print("Files to be created:")
        print("  • .env           (editable configuration)")
        print("  • sys_const.yaml (system constants)")
        print()
        print("Benefits:")
        print("  • Settings persist across runtime restarts")
        print("  • Easy to edit configurations")
        print("  • Shareable across projects")
        print()
        print("="*60 + "\n")
    
    # Ask for confirmation if interactive
    if interactive:
        try:
            response = input("Install USEKIT to Google Drive? (Y/n): ").strip().lower()
            if response and response not in ['y', 'yes', '']:
                print("[INFO] Setup cancelled - using volatile mode")
                print("[INFO] Settings will be lost after runtime restart")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Setup cancelled")
            return False
    
    # Copy files
    if verbose:
        print("[USEKIT] Installing setup files...")
    
    success = _copy_setup_files(setup_path, verbose=verbose)
    
    if success:
        # Set environment variable
        os.environ["ENV_BASE_PATH"] = str(setup_path.parent)
        
        if verbose:
            print()
            print("="*60)
            print("[USEKIT] ✓ Setup Complete!")
            print("="*60)
            print()
            print(f"Location: {setup_path}")
            print()
            print("You can now edit:")
            print(f"  • {setup_path}/.env")
            print(f"  • {setup_path}/sys_const.yaml")
            print()
            print("Start using USEKIT:")
            print("  >>> import usekit as u")
            print("  >>> data = u.rjb('config')")
            print()
            print("="*60 + "\n")
        
        return True
    else:
        if verbose:
            print("[ERROR] Setup failed")
        return False


def setup_colab_volatile(verbose: bool = True) -> bool:
    """
    Setup USEKIT in volatile mode (/content)
    
    Settings will be lost after runtime restart.
    
    Args:
        verbose: Print detailed information
    
    Returns:
        bool: True if setup succeeded
    """
    if not is_colab():
        if verbose:
            print("[USEKIT] Not running in Google Colab environment")
        return False
    
    setup_path = get_volatile_setup_path()
    
    if verbose:
        print("\n" + "="*60)
        print("[USEKIT] Volatile Mode Setup")
        print("="*60)
        print()
        print(f"Location: {setup_path}")
        print()
        print("⚠️  WARNING: Settings will be lost after runtime restart")
        print()
        print("="*60 + "\n")
    
    success = _copy_setup_files(setup_path, verbose=verbose)
    
    if success:
        os.environ["ENV_BASE_PATH"] = str(setup_path.parent)
        if verbose:
            print("[OK] Volatile mode ready")
        return True
    else:
        if verbose:
            print("[ERROR] Setup failed")
        return False


def auto_setup_on_import():
    """
    Auto-detect and show warning (NO input on import)
    
    Called during module import - only shows guidance message.
    User must call use.colab() explicitly for actual setup.
    
    This follows the Termux pattern: warn on import, setup on explicit call.
    """
    if not is_colab():
        return
    
    # Check current status
    status = check_setup_status(verbose=False)
    
    # Already ready - nothing to do
    if status['ready']:
        return
    
    # Drive mounted but not installed - WARN ONLY (no input)
    if status['drive_mounted']:
        print()
        print("="*60)
        print("[USEKIT] Google Drive Detected - Setup Required")
        print("="*60)
        print()
        print(f"Setup location: {get_drive_setup_path()}")
        print()
        print("To install USEKIT for persistent storage:")
        print("  >>> from usekit import use")
        print("  >>> use.colab()")
        print()
        print("(Current mode: Volatile - settings lost on restart)")
        print("="*60 + "\n")
    
    # No drive mount - warn about volatile mode
    else:
        print()
        print("="*60)
        print("[USEKIT] Volatile Mode (Drive Not Mounted)")
        print("="*60)
        print()
        print("⚠️  Settings will be lost after runtime restart")
        print()
        print("For persistent storage:")
        print("  1. Mount Drive:  from google.colab import drive")
        print("                   drive.mount('/content/drive')")
        print("  2. Setup USEKIT: from usekit import use")
        print("                   use.colab()")
        print()
        print("="*60 + "\n")


def warn_if_not_ready():
    """
    Check setup status and warn user if not ready
    
    This is called automatically on import in Colab environments.
    Shows warning message only - no interactive input.
    """
    if not is_colab():
        return
    
    status = check_setup_status(verbose=False)
    
    if status['ready']:
        return
    
    # Not ready - show warning (same as auto_setup_on_import)
    auto_setup_on_import()


# Convenience functions for use.py
def colab(force: bool = False, verbose: bool = True, interactive: bool = True) -> bool:
    """
    Convenience wrapper for setup_colab_drive
    
    Usage:
        >>> from usekit import use
        >>> use.colab()
    """
    return setup_colab_drive(force=force, verbose=verbose, interactive=interactive)


def check(verbose: bool = True) -> Dict[str, any]:
    """
    Check USEKIT Colab environment status
    
    Usage:
        >>> from usekit import use
        >>> use.check()
    """
    return check_setup_status(verbose=verbose)
