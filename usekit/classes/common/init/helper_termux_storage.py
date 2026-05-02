# Path: usekit.classes.common.init.helper_termux_storage.py
# ----------------------------------------------------------------------------------------------- 
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- 

"""
Termux Storage Permission Helper

Provides user-friendly setup for Termux external storage access.
"""

import os
import subprocess
import sys
from pathlib import Path


def is_termux() -> bool:
    """Check if running in Termux environment"""
    # Check environment variables
    if os.environ.get('TERMUX_VERSION'):
        return True
    
    # Check typical Termux paths
    termux_indicators = [
        Path('/data/data/com.termux'),
        Path.home() / '.termux',
    ]
    
    for indicator in termux_indicators:
        if indicator.exists():
            return True
    
    # Check PREFIX variable
    prefix = os.environ.get('PREFIX', '')
    if 'com.termux' in prefix:
        return True
    
    return False


def check_storage_permission() -> bool:
    """
    Check if external storage is accessible
    
    Returns:
        bool: True if storage is accessible with write permission
    """
    try:
        # Check if path exists and is writable
        storage_path = Path('/storage/emulated/0')
        
        if not storage_path.exists():
            return False
        
        # Try to check write permission
        return os.access(storage_path, os.W_OK)
        
    except Exception:
        return False


def check_storage_status(verbose: bool = False) -> dict:
    """
    Get detailed storage permission status
    
    Args:
        verbose: Print status information
    
    Returns:
        dict: Status information
    """
    status = {
        'is_termux': is_termux(),
        'storage_exists': Path('/storage/emulated/0').exists(),
        'storage_writable': check_storage_permission(),
        'ready': False
    }
    
    status['ready'] = status['is_termux'] and status['storage_writable']
    
    if verbose:
        print("\n" + "="*60)
        print("[USEKIT] Storage Permission Status")
        print("="*60)
        print(f"  Termux Environment: {'✓' if status['is_termux'] else '✗'}")
        print(f"  Storage Exists:     {'✓' if status['storage_exists'] else '✗'}")
        print(f"  Storage Writable:   {'✓' if status['storage_writable'] else '✗'}")
        print(f"  Overall Status:     {'READY ✓' if status['ready'] else 'NOT READY ✗'}")
        print("="*60 + "\n")
    
    return status


def setup_termux_storage(verbose: bool = True, interactive: bool = True) -> bool:
    """
    Setup Termux external storage permissions
    
    This will request Android storage permissions and set up access
    to /storage/emulated/0 for file operations.
    
    Args:
        verbose: Print detailed information
        interactive: Ask for user confirmation before proceeding
    
    Returns:
        bool: True if setup succeeded
    
    Examples:
        >>> setup_termux_storage()
        [USEKIT] Running termux-setup-storage...
        ✓ Permission granted! Please restart Python.
    """
    # Check if in Termux
    if not is_termux():
        if verbose:
            print("[USEKIT] Not running in Termux environment")
        return False
    
    # Check if already has permission
    if check_storage_permission():
        if verbose:
            print("[USEKIT] ✓ External storage already accessible")
        _register_editor_autostart(verbose=verbose)
        return True
    
    # Show explanation if verbose
    if verbose:
        print("\n" + "="*60)
        print("[USEKIT] External Storage Setup Required")
        print("="*60)
        print()
        print("USEKIT needs access to external storage to:")
        print("  • Save files to /storage/emulated/0")
        print("  • Access files from other Android apps")
        print("  • Create and manage project folders")
        print("  • Share data with file managers")
        print()
        print("This will prompt for Android storage permission.")
        print("Please grant the permission when asked.")
        print()
        print("="*60 + "\n")
    
    # Ask for confirmation if interactive
    if interactive:
        try:
            response = input("Continue? [Y/n]: ").strip().lower()
            if response and response not in ['y', 'yes']:
                print("[USEKIT] Setup cancelled by user")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\n[USEKIT] Setup cancelled")
            return False
    
    # Run termux-setup-storage
    if verbose:
        print("[USEKIT] Running termux-setup-storage...")
        print("[USEKIT] (A permission dialog will appear)")
    
    try:
        result = subprocess.run(
            ['termux-setup-storage'],
            capture_output=False,
            check=True
        )
        
        # Success message
        if verbose:
            print()
            print("="*60)
            print("[USEKIT] ✓ Permission Granted Successfully!")
            print("="*60)
            print()
            print("Storage access has been configured.")
            print()
            print("IMPORTANT: Please restart Python for changes to take effect:")
            print("  1. Exit Python:    exit()")
            print("  2. Restart Python: python")
            print()
            print("After restarting, you can verify with:")
            print("  >>> from usekit import use")
            print("  >>> use.check()")
            print()
            print("="*60 + "\n")
        
        # .bashrc 에디터 자동실행 등록
        _register_editor_autostart(verbose=verbose)

        return True
        
    except subprocess.CalledProcessError as e:
        # Command failed
        if verbose:
            print()
            print("="*60)
            print("[USEKIT] ✗ Setup Failed")
            print("="*60)
            print()
            print(f"Error: {e}")
            print()
            print("Manual setup steps:")
            print("  1. Exit Python:    exit()")
            print("  2. Run command:    termux-setup-storage")
            print("  3. Grant permission when Android prompts you")
            print("  4. Restart Python: python")
            print()
            print("="*60 + "\n")
        return False
        
    except FileNotFoundError:
        # termux-setup-storage command not found
        if verbose:
            print()
            print("="*60)
            print("[USEKIT] ✗ Command Not Found")
            print("="*60)
            print()
            print("The 'termux-setup-storage' command was not found.")
            print()
            print("Possible causes:")
            print("  • Not running in Termux")
            print("  • Termux is outdated (please update)")
            print()
            print("Please ensure you are running in Termux and try:")
            print("  pkg update && pkg upgrade")
            print()
            print("="*60 + "\n")
        return False
        
    except KeyboardInterrupt:
        if verbose:
            print("\n[USEKIT] Setup cancelled by user")
        return False


def warn_if_not_ready():
    """
    Check storage permission and warn user if not ready
    
    This is called automatically on import in Termux environments.
    """
    if not is_termux():
        return
    
    if check_storage_permission():
        return
    
    # Not ready - show warning
    print()
    print("="*60)
    print("[USEKIT] External Storage: NOT READY")
    print("="*60)
    print()
    print("USEKIT requires external storage permission to work properly.")
    print()
    print("Quick fix:")
    print("  >>> from usekit import use")
    print("  >>> use.termux()")
    print()
    print("Or manually in shell:")
    print("  $ termux-setup-storage")
    print()
    print("="*60 + "\n")


def _register_editor_autostart(verbose: bool = True) -> None:
    """
    .bashrc에 에디터 자동실행 등록 + pip install -e 실행
    """
    bashrc = Path.home() / '.bashrc'
    autostart_line = 'nohup python -c "from usekit import u; u.editor()" > $TMPDIR/editor.log 2>&1 &'

    # .bashrc 등록
    already = False
    if bashrc.exists():
        content = bashrc.read_text()
        if 'u.editor()' in content:
            already = True

    if not already:
        with open(bashrc, 'a') as f:
            f.write(f'\n{autostart_line}\n')
        if verbose:
            print("[USEKIT] ✓ .bashrc에 에디터 자동실행 등록 완료")
    else:
        if verbose:
            print("[USEKIT] ✓ .bashrc 이미 등록됨")

    # 에디터 pip install -e
    try:
        import usekit.tools.editor  # type: ignore
        editor_path = Path(usekit.tools.editor.__file__).parent
        result = subprocess.run(
            ['pip', 'install', '-e', str(editor_path)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            if verbose:
                print("[USEKIT] ✓ 에디터 설치 완료")
        else:
            if verbose:
                print("[USEKIT] △ 에디터 설치 스킵 (이미 설치됨 또는 불필요)")
    except Exception:
        pass  # 에디터 경로 없으면 스킵


# Convenience function for use.py
def termux(verbose: bool = True, interactive: bool = True) -> bool:
    """
    Convenience wrapper for setup_termux_storage
    
    Usage:
        >>> from usekit import use
        >>> use.termux()
    """
    return setup_termux_storage(verbose=verbose, interactive=interactive)


def check(verbose: bool = True) -> dict:
    """
    Check USEKIT environment status
    
    Usage:
        >>> from usekit import use
        >>> use.check()
    """
    return check_storage_status(verbose=verbose)
