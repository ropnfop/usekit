# Path: usekit.classes.wrap.base.use_Interface.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Version: v1.0-unified-init (2025-01-18)
# — memory is emotion, speed is essence —
# -----------------------------------------------------------------------------------------------
"""
USEKIT Environment Setup Interface

Unified interface for initializing USEKIT across different platforms:
- Termux (Android)
- Google Colab
- Local development

Examples:
    >>> from usekit import use
    
    # Termux setup
    >>> use.termux()
    
    # Colab setup
    >>> use.colab()
    
    # Check environment
    >>> use.check()
"""

from typing import Dict, Optional


def termux(verbose: bool = True, interactive: bool = True) -> bool:
    """
    Initialize USEKIT for Termux (Android terminal emulator)
    
    Sets up external storage access and creates minimal configuration.
    
    Args:
        verbose: Show detailed setup information
        interactive: Ask for user confirmation
    
    Returns:
        bool: True if setup succeeded
    
    Examples:
        >>> from usekit import use
        >>> use.termux()
        [USEKIT] Running termux-setup-storage...
        ✓ Permission granted!
    """
    try:
        from usekit.classes.common.init.helper_termux_storage import termux as setup_termux
        return setup_termux(verbose=verbose, interactive=interactive)
    except ImportError as e:
        if verbose:
            print(f"[ERROR] Failed to import helper_termux_storage: {e}")
        return False


def colab(force: bool = False, verbose: bool = True, interactive: bool = True) -> bool:
    """
    Initialize USEKIT for Google Colab
    
    Sets up persistent storage in Google Drive or volatile mode in /content.
    
    Args:
        force: Reinstall even if already exists
        verbose: Show detailed setup information
        interactive: Ask for user confirmation
    
    Returns:
        bool: True if setup succeeded
    
    Examples:
        >>> from usekit import use
        >>> use.colab()
        [USEKIT] Google Drive detected
        Install to Drive? (Y/n): y
        ✓ Setup complete!
    """
    try:
        from usekit.classes.common.init.helper_colab_setup import colab as setup_colab
        return setup_colab(force=force, verbose=verbose, interactive=interactive)
    except ImportError as e:
        if verbose:
            print(f"[ERROR] Failed to import helper_colab_setup: {e}")
        return False


def check(verbose: bool = True) -> Dict[str, any]:
    """
    Check USEKIT environment status
    
    Automatically detects environment (Termux, Colab, or local) and
    shows relevant status information.
    
    Args:
        verbose: Print status information
    
    Returns:
        dict: Environment status details
    
    Examples:
        >>> from usekit import use
        >>> status = use.check()
        [USEKIT] Colab Environment Status
        ==========================================
          Colab Environment:  ✓
          Drive Mounted:      ✓
          Setup Location:     /content/drive/MyDrive/PROJECTS/upj/usekit
          Overall Status:     READY ✓
    """
    try:
        # Try Colab first
        from usekit.classes.core.env.loader_env import is_colab
        if is_colab():
            from usekit.classes.common.init.helper_colab_setup import check as check_colab
            return check_colab(verbose=verbose)
        
        # Try Termux
        from usekit.classes.core.env.loader_env import is_termux
        if is_termux():
            from usekit.classes.common.init.helper_termux_storage import check as check_termux
            return check_termux(verbose=verbose)
        
        # Local environment
        if verbose:
            print("\n" + "="*60)
            print("[USEKIT] Local Environment")
            print("="*60)
            print("  Platform: Desktop/Server")
            print("  Status:   Ready for development")
            print("="*60 + "\n")
        
        return {
            'platform': 'local',
            'ready': True
        }
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to check environment: {e}")
        return {
            'platform': 'unknown',
            'ready': False,
            'error': str(e)
        }


def editor(data: Optional[str] = None,
           name: Optional[str] = None,
           dir_path: Optional[str] = None,
           **kwargs) -> bool:
    """
    Launch USEKIT web editor (Termux local server).

    Args:
        data:     초기 내용 or 단순이름 (fpb resolve 시도)
        name:     파일명 e.g. "test03" or "test03.py"
        dir_path: 저장 디렉토리 e.g. "/storage/.../src/base/"

    Examples:
        u.editor()                              # default
        u.editor("test01")                      # fpb resolve
        u.editor(data, "test03")                # 내용 + 파일명
        u.editor(data, "test03", "/storage/..") # 내용 + 파일명 + 디렉토리

    Returns:
        bool: True if launch succeeded (best-effort)
    """
    try:
        from usekit.tools.editor.use_editor import run
        run(data=data, name=name, dir_path=dir_path, **kwargs)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to launch editor: {e}")
        return False


def help():
    """
    Show USEKIT setup help
    
    Examples:
        >>> from usekit import use
        >>> use.help()
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    USEKIT Setup Guide                        ║
╚══════════════════════════════════════════════════════════════╝

Platform-Specific Setup:
────────────────────────────────────────────────────────────────

[Termux (Android)]
  Setup external storage access:
    >>> from usekit import use
    >>> use.termux()
  
  This will:
    • Request Android storage permission
    • Setup /storage/emulated/0 access
    • Create minimal configuration

[Google Colab]
  Setup persistent Drive storage:
    >>> from usekit import use
    >>> use.colab()
  
  This will:
    • Check Google Drive mount status
    • Install to Drive (persistent) or /content (volatile)
    • Create .env and sys_const.yaml for editing

[Local Development]
  No setup needed - just import and use:
    >>> import usekit as u
    >>> data = u.rjb("config")

Common Commands:
────────────────────────────────────────────────────────────────
  use.check()     - Check environment status
  use.termux()    - Setup Termux environment
  use.colab()     - Setup Colab environment
  use.help()      - Show this help message

For more info: https://github.com/yourusername/usekit
""")


# Convenience exports
__all__ = [
    'termux',
    'colab', 
    'check',
    'help',
    'editor',
]
