# Path: usekit.classes.core.env.base.resolver_path.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- #

"""
Path Resolution Module for USEKIT

Handles intelligent detection of project root and base paths
using multiple strategies in priority order.
"""

import os
from pathlib import Path
from typing import Optional, List


# Project marker files (in priority order)
PROJECT_MARKERS = [
    '.usekit',           # USEKIT-specific marker (highest priority)
    '.git',              # Git repository
    'setup.py',          # Python package
    'pyproject.toml',    # Modern Python package
    'requirements.txt',  # Python dependencies
    'Pipfile',           # Pipenv project
    'README.md',         # Documentation root
]


def find_project_root(
    start_path: Optional[Path] = None,
    max_depth: int = 5,
    markers: Optional[List[str]] = None
) -> Optional[Path]:
    """
    Find project root by searching for marker files
    
    Args:
        start_path: Starting directory (default: current directory)
        max_depth: Maximum levels to search upward
        markers: List of marker files to search for (default: PROJECT_MARKERS)
    
    Returns:
        Optional[Path]: Project root path, or None if not found
    
    Examples:
        >>> root = find_project_root()
        >>> if root:
        ...     print(f"Project root: {root}")
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    if markers is None:
        markers = PROJECT_MARKERS
    
    # Search current directory and parents
    search_paths = [start_path] + list(start_path.parents[:max_depth])
    
    for path in search_paths:
        for marker in markers:
            marker_path = path / marker
            if marker_path.exists():
                return path
    
    return None


def find_env_file_path(
    start_path: Optional[Path] = None,
    env_filename: str = '.env',
    max_depth: int = 5
) -> Optional[Path]:
    """
    Search for .env file in current and parent directories
    
    Args:
        start_path: Starting directory (default: current directory)
        env_filename: Name of env file to search for
        max_depth: Maximum levels to search upward
    
    Returns:
        Optional[Path]: Path to .env file, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    # Search current directory and parents
    search_paths = [start_path] + list(start_path.parents[:max_depth])
    
    for path in search_paths:
        env_path = path / env_filename
        if env_path.exists() and env_path.is_file():
            return env_path
    
    return None


def resolve_base_path_from_env(
    env_path: Optional[Path] = None,
    verbose: bool = False
) -> Optional[Path]:
    """
    Extract and resolve ENV_BASE_PATH from .env file
    
    Args:
        env_path: Path to .env file (if None, searches for it)
        verbose: Print resolution details
    
    Returns:
        Optional[Path]: Resolved base path, or None if not found
    """
    if env_path is None:
        env_path = find_env_file_path()
    
    if env_path is None:
        return None
    
    try:
        # Parse .env file manually (avoid dotenv dependency here)
        base_path_value = None
        
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if key == 'ENV_BASE_PATH':
                        base_path_value = value
                        break
        
        if base_path_value:
            resolved = Path(base_path_value).expanduser().resolve()
            
            if resolved.exists():
                if verbose:
                    print(f"Resolved ENV_BASE_PATH: {resolved}")
                return resolved
            else:
                if verbose:
                    print(f"Warning: ENV_BASE_PATH exists in .env but path not found: {resolved}")
        
    except Exception as e:
        if verbose:
            print(f"Error reading .env file: {e}")
    
    return None


def resolve_base_path_priority(
    verbose: bool = False
) -> Optional[Path]:
    """
    Resolve base path using priority strategy:
    1. ENV_BASE_PATH environment variable
    2. ENV_BASE_PATH from .env file
    3. Project root (marker-based detection)
    
    Args:
        verbose: Print resolution steps
    
    Returns:
        Optional[Path]: Resolved base path
    """
    # Priority 1: Environment variable
    env_var = os.environ.get('ENV_BASE_PATH')
    if env_var:
        path = Path(env_var).expanduser().resolve()
        if path.exists():
            if verbose:
                print(f"Base path from ENV_BASE_PATH: {path}")
            return path
        elif verbose:
            print(f"Warning: ENV_BASE_PATH set but path not found: {path}")
    
    # Priority 2: .env file
    env_file_path = resolve_base_path_from_env(verbose=verbose)
    if env_file_path:
        return env_file_path
    
    # Priority 3: Project root
    project_root = find_project_root()
    if project_root:
        if verbose:
            print(f"Base path from project root: {project_root}")
        return project_root
    
    if verbose:
        print("No base path resolved via priority strategy")
    
    return None


def get_usekit_install_path() -> Path:
    """
    Get the installation path of USEKIT package
    
    Returns:
        Path: Absolute path to USEKIT installation
    """
    return Path(__file__).parent.resolve()


def is_development_mode() -> bool:
    """
    Check if USEKIT is running in development mode (not pip-installed)
    
    Returns:
        bool: True if development mode
    """
    install_path = get_usekit_install_path()
    
    # Check if path contains site-packages or dist-packages
    path_str = str(install_path)
    return not ('site-packages' in path_str or 'dist-packages' in path_str)


def resolve_relative_to_base(
    relative_path: str,
    base_path: Optional[Path] = None
) -> Path:
    """
    Resolve a relative path against base path
    
    Args:
        relative_path: Relative path string
        base_path: Base path to resolve against (default: resolved base)
    
    Returns:
        Path: Absolute resolved path
    """
    if base_path is None:
        base_path = resolve_base_path_priority()
        if base_path is None:
            base_path = Path.cwd()
    
    # Handle @ prefix (USEKIT coordinate system)
    if relative_path.startswith('@'):
        relative_path = relative_path[1:].lstrip('/')
    
    return (base_path / relative_path).resolve()


def validate_path_exists(
    path: Path,
    path_type: str = "path",
    create_if_missing: bool = False
) -> bool:
    """
    Validate that a path exists, optionally creating it
    
    Args:
        path: Path to validate
        path_type: Description of path type for error messages
        create_if_missing: Create directory if it doesn't exist
    
    Returns:
        bool: True if path exists or was created
    """
    if path.exists():
        return True
    
    if create_if_missing:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Warning: Could not create {path_type}: {e}")
            return False
    
    return False


def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path (expand user, resolve, absolute)
    
    Args:
        path: Path string or Path object
    
    Returns:
        Path: Normalized absolute path
    """
    return Path(path).expanduser().resolve()
