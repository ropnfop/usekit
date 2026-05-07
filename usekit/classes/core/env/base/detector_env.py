# Path: usekit.classes.core.env.base.detector_env.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- #

"""
Environment Detection Module for USEKIT

Detects execution environment (Colab, Termux, Desktop) and provides
appropriate default paths for each environment.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Literal, Optional
from functools import lru_cache

EnvType = Literal['colab', 'termux', 'desktop', 'unknown']


# ───────────────────────────────────────────────────────────────
# Auto-install dependencies
# ───────────────────────────────────────────────────────────────
_dotenv_checked = False
_yaml_checked = False


def ensure_dotenv():
    """Lazy-load and auto-install python-dotenv if needed"""
    global _dotenv_checked
    if _dotenv_checked:
        return
    
    try:
        import dotenv  # noqa
    except ImportError:
        print("[SETUP] Installing python-dotenv...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "python-dotenv>=0.10.0", 
            "--no-deps"
        ])
    
    _dotenv_checked = True


def ensure_yaml():
    """Lazy-load and auto-install PyYAML if needed"""
    global _yaml_checked
    if _yaml_checked:
        return

    try:
        import yaml  # noqa
    except ImportError:
        print("[SETUP] Installing PyYAML...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "pyyaml>=5.1",
            "--no-deps"
        ])
        import yaml  # noqa: F401

    _yaml_checked = True


@lru_cache(maxsize=1)
def detect_environment() -> EnvType:
    """
    Detect current execution environment
    
    Returns:
        EnvType: One of 'colab', 'termux', 'desktop', 'unknown'
    
    Examples:
        >>> env = detect_environment()
        >>> if env == 'colab':
        ...     print("Running in Google Colab")
    """
    # Colab detection
    if _is_colab():
        return 'colab'
    
    # Termux detection
    if _is_termux():
        return 'termux'
    
    # Desktop/server environment
    if _is_desktop():
        return 'desktop'
    
    return 'unknown'


@lru_cache(maxsize=1)
def _is_colab() -> bool:
    """Check if running in Google Colab"""
    try:
        import google.colab
        return True
    except ImportError:
        return False


@lru_cache(maxsize=1)
def _is_termux() -> bool:
    """Check if running in Termux (Android terminal emulator)"""
    # Check Termux-specific paths
    if os.path.exists('/data/data/com.termux'):
        return True
    
    # Check Termux environment variables
    if os.environ.get('TERMUX_VERSION'):
        return True
    
    # Check PREFIX variable
    prefix = os.environ.get('PREFIX', '')
    if 'com.termux' in prefix:
        return True
    
    # Check home directory path
    home = str(Path.home())
    if '/data/data/com.termux' in home:
        return True
    
    return False


@lru_cache(maxsize=1)
def _is_desktop() -> bool:
    """Check if running in desktop/server environment"""
    # Simple heuristic: not Colab, not Termux, has HOME or USERPROFILE
    return bool(os.environ.get('HOME') or os.environ.get('USERPROFILE'))


def get_default_paths(env_type: EnvType) -> list[Path]:
    """
    Get default base paths for given environment type
    
    Args:
        env_type: Environment type from detect_environment()
    
    Returns:
        list[Path]: List of potential base paths in priority order
    
    Examples:
        >>> paths = get_default_paths('termux')
        >>> # [Path('/storage/emulated/0'), Path('~/projects'), ...]
    """
    if env_type == 'colab':
        return _get_colab_defaults()
    elif env_type == 'termux':
        return _get_termux_defaults()
    elif env_type == 'desktop':
        return _get_desktop_defaults()
    else:
        return []


def _get_colab_defaults() -> list[Path]:
    """Get default paths for Google Colab environment"""
    paths = []
    
    # Google Drive mounted location
    drive_path = Path('/content/drive/MyDrive')
    if drive_path.exists():
        paths.append(drive_path)
    
    # Colab content directory
    content_path = Path('/content')
    if content_path.exists():
        paths.append(content_path)
    
    return paths


def _get_termux_defaults() -> list[Path]:
    """Get default paths for Termux environment"""
    paths = []
    home = Path.home()
    
    # Shared storage (accessible from Android file manager)
    shared_storage = home / 'storage' / 'shared'
    if shared_storage.exists():
        paths.append(shared_storage)
    
    # Projects folder (common convention)
    projects = home / 'projects'
    if projects.exists():
        paths.append(projects)
    
    # Termux home directory
    paths.append(home)
    
    return paths


def _get_desktop_defaults() -> list[Path]:
    """Get default paths for desktop environment"""
    # Current working directory
    return [Path.cwd()]


def get_environment_info() -> dict:
    """
    Get comprehensive environment information
    
    Returns:
        dict: Environment details including type, defaults, and paths
    
    Examples:
        >>> info = get_environment_info()
        >>> print(info['type'])  # 'termux'
        >>> print(info['home'])  # Path('/data/data/com.termux/files/home')
    """
    env_type = detect_environment()
    
    return {
        'type': env_type,
        'home': Path.home(),
        'cwd': Path.cwd(),
        'default_paths': get_default_paths(env_type),
        'is_colab': env_type == 'colab',
        'is_termux': env_type == 'termux',
        'is_desktop': env_type == 'desktop',
    }


def suggest_base_path() -> Optional[Path]:
    """
    Suggest appropriate base path for current environment
    
    Returns:
        Optional[Path]: Suggested base path, or None if no suitable path found
    
    Examples:
        >>> path = suggest_base_path()
        >>> print(f"Suggested: {path}")
    """
    env_type = detect_environment()
    default_paths = get_default_paths(env_type)
    
    # Return first existing path
    for path in default_paths:
        if path.exists():
            return path
    
    return None


def is_interactive_environment() -> bool:
    """
    Check if running in interactive environment (Colab, Jupyter, etc.)
    
    Returns:
        bool: True if interactive environment detected
    """
    # Check for Colab
    if _is_colab():
        return True
    
    # Check for Jupyter
    try:
        get_ipython()  # type: ignore
        return True
    except NameError:
        return False


def get_pip_installation_path() -> Optional[Path]:
    """
    Detect if USEKIT is installed via pip and return installation path
    
    Returns:
        Optional[Path]: Installation path if pip-installed, None otherwise
    """
    current_file = Path(__file__).resolve()
    
    # Check for site-packages or dist-packages in path
    site_packages_indicators = ['site-packages', 'dist-packages']
    
    for indicator in site_packages_indicators:
        if indicator in str(current_file):
            # Find the site-packages directory
            parts = current_file.parts
            try:
                idx = parts.index(indicator)
                return Path(*parts[:idx+1])
            except ValueError:
                continue
    
    return None


@lru_cache(maxsize=1)
def is_pip_installed() -> bool:
    """
    Check if USEKIT is installed via pip
    
    Returns:
        bool: True if pip-installed
    """
    return get_pip_installation_path() is not None
