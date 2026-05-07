# Path: usekit/classes/core/env/loader_env.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Version: v4.1-termux-support (2025-01-08)
# — memory is emotion, speed is essence —
# -----------------------------------------------------------------------------------------------
# Purpose:
#   Universal environment loader with dynamic path calculation from .env
#   - No hardcoded paths in sys_const.yaml needed
#   - BASE_PATH and USEKIT_PATH auto-calculated from ENV_BASE_PATH
#   - Auto-detects Termux and uses /storage/emulated/0/projects/pj01 as default
#   - Lazy evaluation + auto .env creation with smart path binding
#   - Import time: <0.001s (was ~1.5s)
# -----------------------------------------------------------------------------------------------

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

# ───────────────────────────────────────────────────────────────
# [1] Lazy dependency loading
# ───────────────────────────────────────────────────────────────
_dotenv_checked = False

def _ensure_dotenv():
    """Lazy-load dotenv only when needed."""
    global _dotenv_checked
    if _dotenv_checked:
        return
    
    try:
        import dotenv  # noqa
    except ImportError:
        print("[SETUP] Installing python-dotenv...")
        # Use relaxed version to avoid conflicts
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "python-dotenv>=0.10.0", 
            "--no-deps"  # Skip dependency checking to avoid conflicts
        ])
    
    _dotenv_checked = True
    
# ───────────────────────────────────────────────────────────────
_yaml_checked = False

def _ensure_yaml():
    """Lazy-load PyYAML only when needed."""
    global _yaml_checked
    if _yaml_checked:
        return

    try:
        import yaml  # noqa
    except ImportError:
        print("[SETUP] Installing PyYAML...")
        # Use relaxed version to avoid conflicts
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "pyyaml>=5.1",
            "--no-deps"  # Skip dependency checking to avoid conflicts
        ])
        import yaml  # noqa: F401

    _yaml_checked = True
    
# ───────────────────────────────────────────────────────────────
# [2] Environment detection (cached)
# ───────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def is_colab() -> bool:
    """Check if running in Google Colab."""
    try:
        import google.colab  # noqa
        return True
    except ImportError:
        return False

@lru_cache(maxsize=1)
def is_pip_env() -> bool:
    """
    Check if USEKIT is installed via pip.
    
    Returns:
        True if installed via pip (site-packages), False otherwise
    """
    try:
        usekit_path = Path(__file__).resolve()
        return 'site-packages' in str(usekit_path)
    except:
        return False

@lru_cache(maxsize=1)
def is_termux() -> bool:
    """Check if running in Termux (Android terminal emulator)."""
    # Method 1: Check for Termux-specific environment variable
    if os.getenv("TERMUX_VERSION"):
        return True
    
    # Method 2: Check for typical Termux paths
    termux_indicators = [
        Path("/data/data/com.termux"),
        Path.home() / ".termux",
    ]
    
    for indicator in termux_indicators:
        if indicator.exists():
            return True
    
    # Method 3: Check if PREFIX points to Termux location
    prefix = os.getenv("PREFIX", "")
    if "com.termux" in prefix:
        return True
    
    return False

# ───────────────────────────────────────────────────────────────
# [3] Fast project root detection with smart caching
# ───────────────────────────────────────────────────────────────
_project_root_cache: Optional[Path] = None

def detect_project_root() -> Path:
    """
    Detect project root with optimized search strategy.
    Supports encapsulated .env inside usekit/ directory.
    
    Priority:
    1. ENV_BASE_PATH environment variable (set by .env)
    2. For pip installs: ~/project/usekit (not ~/projects/pj01/usekit)
    3. Find usekit directory, then go up one level (dev mode only)
    4. Environment-specific defaults (Colab, Termux, local)
    
    USEKIT Encapsulation Pattern:
        project/              ← BASE_PATH (this is returned)
        └── usekit/         ← USEKIT package
            ├── .env          ← USEKIT config (encapsulated)
            ├── sys/
            │   └── sys_yaml/
            │       └── sys_const.yaml
            └── classes/
                └── core/
                    └── env/
                        └── loader_env.py  ← this file
    
    Note: For pip-installed USEKIT, ENV_BASE_PATH will be set by auto_copy process.
    """
    global _project_root_cache
    if _project_root_cache is not None:
        return _project_root_cache
    
    # Strategy 1: Check ENV_BASE_PATH first (fastest)
    env_base = os.getenv("ENV_BASE_PATH")
    if env_base:
        path = Path(env_base).resolve()
        if path.exists():
            _project_root_cache = path
            return path
    
    # Strategy 2: For pip installs, return base directory (not usekit subdirectory)
    if is_pip_env():
        if is_termux():
            base_dir = Path("/storage/emulated/0/projects/pj01")
        else:
            base_dir = Path.home() / "projects" / "pj01"
        
        _project_root_cache = base_dir
        return base_dir
    
    # Strategy 3: Development mode - Find usekit directory, go up one level
    # This file is at: usekit/classes/core/env/loader_env.py
    # We need to find 'usekit' directory, then its parent is BASE_PATH
    current = Path(__file__).resolve()
    
    # Walk up until we find a directory named 'usekit'
    for parent in current.parents:
        if parent.name == "usekit":
            # Found usekit directory - its parent is BASE_PATH
            base_path = parent.parent
            _project_root_cache = base_path
            return base_path
    
    # Fallback: Assume standard depth (4 levels up from this file)
    # usekit/classes/core/env/loader_env.py → ../../../../ → project/
    if len(current.parents) >= 5:
        _project_root_cache = current.parents[4]
        return current.parents[4]
    
    # Strategy 4: Environment-specific defaults
    if is_termux():
        # Termux: Use Android external storage
        android_storage = Path("/storage/emulated/0/projects/pj01")
        try:
            android_storage.mkdir(parents=True, exist_ok=True)
            _project_root_cache = android_storage
            return android_storage
        except:
            # Fallback to termux home if storage creation fails
            termux_home = Path.home() / "projects" / "pj01"
            termux_home.mkdir(parents=True, exist_ok=True)
            _project_root_cache = termux_home
            return termux_home
    elif is_colab():
        _project_root_cache = Path("/content")
    else:
        _project_root_cache = Path.cwd()
    
    return _project_root_cache

def _infer_base_path_from_context() -> Optional[str]:
    """
    Infer likely BASE_PATH based on OS and execution context.
    
    Priority order:
    1. Termux: /storage/emulated/0/projects/pj01
    2. Colab: /content/drive/MyDrive/PROJECT or /content
    3. Pip: ~/projects/pj01 (base directory, not usekit subdirectory)
    4. Dev: Detect from usekit location
    
    Returns:
        str: Inferred BASE_PATH or None if cannot determine
    """
    # Check if in Termux (Android)
    if is_termux():
        # Termux: Use Android external storage
        android_storage = Path("/storage/emulated/0/projects/pj01")
        
        # Create directory if it doesn't exist
        try:
            android_storage.mkdir(parents=True, exist_ok=True)
            return str(android_storage)
        except:
            # Fallback to termux home if storage creation fails
            termux_home = Path.home() / "projects" / "pj01"
            termux_home.mkdir(parents=True, exist_ok=True)
            return str(termux_home)
    
    # Check if in Colab
    if is_colab():
        # Colab: Check if Google Drive is mounted
        gdrive_base = Path("/content/drive/MyDrive/PROJECTS/pj01")
        if gdrive_base.parent.exists():  # MyDrive exists
            return str(gdrive_base)
        return "/content"
    
    # Check if pip installed
    if is_pip_env():
        # Pip: Use standard project directory structure
        base_dir = Path.home() / "projects" / "pj01"
        base_dir.mkdir(parents=True, exist_ok=True)
        return str(base_dir)
    
    # Development mode: Try to find actual BASE_PATH
    try:
        current = Path(__file__).resolve()
        for parent in current.parents:
            if parent.name == "usekit":
                return str(parent.parent)
    except:
        pass
    
    # Fallback to current directory
    return str(Path.cwd())

def _handle_pip_installation(auto_copy: bool = True, verbose: bool = False) -> Optional[Path]:
    """
    Handle .env file for pip-installed USEKIT.
    
    Creates project structure at ~/projects/pj01/ with:
    - ~/projects/pj01/usekit/.env (from package's .env.example)
    - ~/projects/pj01/usekit/sys/sys_yaml/sys_const.yaml (from package)
    
    The created .env will have ENV_BASE_PATH set to ~/projects/pj01
    
    Args:
        auto_copy: Whether to auto-create .env and sys files
        verbose: Print status messages
        
    Returns:
        Path to .env file if found/created, None otherwise
    """
    # Determine base project directory
    if is_termux():
        base_dir = Path("/storage/emulated/0/projects/pj01")
    else:
        base_dir = Path.home() / "projects" / "pj01"
    
    # Target paths matching project structure
    usekit_dir = base_dir / "usekit"
    target_env = usekit_dir / ".env"
    sys_dir = usekit_dir / "sys" / "sys_yaml"
    target_sys_const = sys_dir / "sys_const.yaml"
    
    # If .env already exists, use it
    if target_env.exists():
        if verbose:
            print(f"[ENV] Using existing .env at: {target_env}")
        # Load the .env to set ENV_BASE_PATH in environment
        _ensure_dotenv()
        from dotenv import load_dotenv
        load_dotenv(target_env, override=True)
        return target_env
    
    # If auto_copy disabled, don't create
    if not auto_copy:
        return None
    
    # Find source files in package
    try:
        # Package installation path
        usekit_install_path = Path(__file__).resolve().parent.parent.parent.parent
        
        # Find .env.example
        example_candidates = [
            usekit_install_path / ".env.example",
            usekit_install_path / "usekit" / ".env.example",
        ]
        
        source_example = None
        for candidate in example_candidates:
            if candidate.exists():
                source_example = candidate
                break
        
        if not source_example:
            if verbose:
                print(f"[WARN] Could not find .env.example in pip package")
                print(f"[INFO] Searched: {example_candidates}")
            return None
        
        # Find sys_const.yaml
        sys_const_candidates = [
            usekit_install_path / "sys" / "sys_yaml" / "sys_const.yaml",
            usekit_install_path / "usekit" / "sys" / "sys_yaml" / "sys_const.yaml",
        ]
        
        source_sys_const = None
        for candidate in sys_const_candidates:
            if candidate.exists():
                source_sys_const = candidate
                break
        
        # Create directory structure
        usekit_dir.mkdir(parents=True, exist_ok=True)
        sys_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy and modify .env.example -> .env
        with open(source_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace or add ENV_BASE_PATH
        lines = content.splitlines()
        modified_lines = []
        has_base_path = False
        
        for line in lines:
            stripped = line.strip()
            # Check for ENV_BASE_PATH line (commented or uncommented)
            if stripped.startswith('ENV_BASE_PATH') or stripped.startswith('# ENV_BASE_PATH'):
                # Replace with base directory (not usekit dir)
                modified_lines.append(f"ENV_BASE_PATH={base_dir}")
                has_base_path = True
                if verbose:
                    print(f"[OK] Auto-bound: ENV_BASE_PATH={base_dir}")
            else:
                modified_lines.append(line)
        
        # Add ENV_BASE_PATH at top if not present
        if not has_base_path:
            modified_lines.insert(0, f"ENV_BASE_PATH={base_dir}")
            modified_lines.insert(1, "")
            if verbose:
                print(f"[OK] Added: ENV_BASE_PATH={base_dir}")
        
        # Write .env
        with open(target_env, 'w', encoding='utf-8') as f:
            f.write('\n'.join(modified_lines) + '\n')
        
        if verbose:
            print(f"[OK] Created .env from package .env.example")
            print(f"[OK] Location: {target_env}")
        
        # Copy sys_const.yaml if found and doesn't exist
        if source_sys_const and not target_sys_const.exists():
            shutil.copy2(source_sys_const, target_sys_const)
            if verbose:
                print(f"[OK] Copied sys_const.yaml")
                print(f"[OK] Location: {target_sys_const}")
        
        # Load the newly created .env
        _ensure_dotenv()
        from dotenv import load_dotenv
        load_dotenv(target_env, override=True)
        
        if verbose:
            print(f"[OK] Project structure initialized at: {base_dir}")
            print(f"[OK] usekit/.env: {target_env.exists()}")
            print(f"[OK] usekit/sys/sys_yaml/sys_const.yaml: {target_sys_const.exists()}")
        
        return target_env
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to auto-create project structure: {e}")
            import traceback
            traceback.print_exc()
        return None

def _create_env_with_inferred_path(base_path: Path, verbose: bool = False) -> bool:
    """
    Create .env from .env.example, automatically filling ENV_BASE_PATH.
    
    Smart binding:
    1. Copies .env.example → .env
    2. Infers appropriate BASE_PATH for current OS/context
    3. Replaces ENV_BASE_PATH= line with inferred path
    
    Args:
        base_path: Directory containing .env.example
        verbose: Print status messages
        
    Returns:
        bool: True if created successfully with auto-binding
    """
    env_file = base_path / ".env"
    example_file = base_path / ".env.example"
    
    # Skip if files don't exist
    if env_file.exists() or not example_file.exists():
        return False
    
    try:
        # Read template
        with open(example_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Infer BASE_PATH for this context
        inferred_path = _infer_base_path_from_context()
        
        if verbose:
            print(f"[INFO] Inferring BASE_PATH for auto-binding...")
            env_type = 'Termux' if is_termux() else 'Colab' if is_colab() else 'pip' if is_pip_env() else 'dev'
            print(f"[INFO] Detected context: {env_type}")
            print(f"[INFO] Inferred path: {inferred_path}")
        
        # Replace ENV_BASE_PATH= with inferred value
        # Handle different formats:
        # ENV_BASE_PATH=
        # ENV_BASE_PATH =
        # # ENV_BASE_PATH=/old/path
        lines = template_content.split('\n')
        modified_lines = []
        binding_applied = False
        
        for line in lines:
            stripped = line.strip()
            # Check if this is the ENV_BASE_PATH line
            if stripped.startswith('ENV_BASE_PATH') or stripped.startswith('# ENV_BASE_PATH'):
                # Replace with auto-bound value
                modified_lines.append(f"ENV_BASE_PATH={inferred_path}")
                binding_applied = True
                if verbose:
                    print(f"[OK] Auto-bound: ENV_BASE_PATH={inferred_path}")
            else:
                modified_lines.append(line)
        
        # Write .env with auto-bound path
        modified_content = '\n'.join(modified_lines)
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        if verbose:
            if binding_applied:
                print(f"[OK] Created .env with auto-binding: {env_file}")
            else:
                print(f"[WARN] Created .env but no ENV_BASE_PATH found to bind")
        
        return binding_applied
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to create .env with auto-binding: {e}")
        return False

# ───────────────────────────────────────────────────────────────
# [4] .env auto-copy helper (legacy - kept for compatibility)
# ───────────────────────────────────────────────────────────────
def _copy_env_example(base_path: Path, verbose: bool = False) -> bool:
    """
    Legacy: Simple copy of .env.example → .env without auto-binding.
    Use _create_env_with_inferred_path for smart auto-binding instead.
    
    Returns:
        bool: True if copied successfully, False otherwise
    """
    env_file = base_path / ".env"
    example_file = base_path / ".env.example"
    
    # Skip if .env already exists
    if env_file.exists():
        return False
    
    # Skip if .env.example doesn't exist
    if not example_file.exists():
        return False
    
    try:
        shutil.copy2(example_file, env_file)
        if verbose:
            print(f"[OK] Created .env from .env.example: {env_file}")
        return True
    except Exception as e:
        if verbose:
            print(f"[WARN] Failed to copy .env.example: {e}")
        return False

# ───────────────────────────────────────────────────────────────
# [5] Fast .env file finder with auto-copy
# ───────────────────────────────────────────────────────────────
_env_file_cache: Optional[Path] = None

def find_env_file(auto_copy: bool = True, verbose: bool = False) -> Optional[Path]:
    """
    Find .env file with caching and optional smart auto-creation.
    
    Smart Auto-Binding:
        If .env doesn't exist but .env.example does:
        1. Copies .env.example → .env
        2. Infers appropriate BASE_PATH for current OS/context
        3. Auto-fills ENV_BASE_PATH= with inferred value
    
    Pip Installation Auto-Copy:
        For pip installations without .env:
        1. Creates ~/projects/pj01/.env from package's .env.example
        2. Sets ENV_BASE_PATH=~/projects/pj01 automatically
        3. Loads environment variables from new .env
    
    USEKIT Encapsulation Pattern:
        Looks for .env in USEKIT_PATH (usekit/.env) for encapsulation,
        falls back to BASE_PATH if not found.
    
    Search locations (in order):
    1. USEKIT_ENV_PATH environment variable
    2. For pip installs: ~/projects/pj01/.env (with auto-copy)
    3. USEKIT_PATH/.env (encapsulated config - PRIMARY for dev)
    4. BASE_PATH/.env (fallback)
    5. Current working directory (last resort)
    
    Args:
        auto_copy: If True, create .env with smart auto-binding if missing
        verbose: Print status messages
        
    Returns:
        Path to .env file, or None if not found
    """
    global _env_file_cache
    if _env_file_cache is not None:
        return _env_file_cache
    
    # Priority 1: Manual override
    manual = os.getenv("USEKIT_ENV_PATH")
    if manual:
        path = Path(manual)
        if path.exists():
            _env_file_cache = path
            return path
    
    # Priority 2: Handle pip installation with auto-copy
    if is_pip_env():
        pip_env = _handle_pip_installation(auto_copy=auto_copy, verbose=verbose)
        if pip_env:
            _env_file_cache = pip_env
            return pip_env
        # If pip install but no auto-copy, continue to other search locations
    
    # Priority 3: Check USEKIT_PATH (encapsulated - PRIMARY location for dev)
    usekit_path = get_usekit_path()
    env_file = usekit_path / ".env"
    example_file = usekit_path / ".env.example"
    
    # Smart auto-creation with path inference
    if auto_copy and not env_file.exists() and example_file.exists():
        if verbose:
            print("[INFO] Creating .env with smart auto-binding...")
        _create_env_with_inferred_path(usekit_path, verbose=verbose)
    
    # Return .env if it exists (either original or newly created)
    if env_file.exists():
        _env_file_cache = env_file
        return env_file
    
    # Fallback to .env.example (read-only mode)
    if example_file.exists():
        if verbose:
            print("[INFO] Using .env.example (read-only mode)")
        _env_file_cache = example_file
        return example_file
    
    # Priority 4: Check BASE_PATH (fallback for non-encapsulated setup)
    base_path = get_base_path()
    if base_path != usekit_path.parent:  # Avoid duplicate check
        base_env = base_path / ".env"
        base_example = base_path / ".env.example"
        
        # Smart auto-creation here too
        if auto_copy and not base_env.exists() and base_example.exists():
            _create_env_with_inferred_path(base_path, verbose=verbose)
        
        if base_env.exists():
            if verbose:
                print("[INFO] Using BASE_PATH/.env (fallback mode)")
            _env_file_cache = base_env
            return base_env
        
        if base_example.exists():
            if verbose:
                print("[INFO] Using BASE_PATH/.env.example (fallback mode)")
            _env_file_cache = base_example
            return base_example
    
    # Priority 5: Check current directory as last resort
    cwd = Path.cwd()
    if cwd != usekit_path and cwd != base_path:
        cwd_env = cwd / ".env"
        cwd_example = cwd / ".env.example"
        
        # Smart auto-creation
        if auto_copy and not cwd_env.exists() and cwd_example.exists():
            _create_env_with_inferred_path(cwd, verbose=verbose)
        
        if cwd_env.exists():
            if verbose:
                print("[INFO] Using cwd/.env (last resort)")
            _env_file_cache = cwd_env
            return cwd_env
        
        if cwd_example.exists():
            if verbose:
                print("[INFO] Using cwd/.env.example (last resort)")
            _env_file_cache = cwd_example
            return cwd_example
    
    return None

# ───────────────────────────────────────────────────────────────
# [6] Lazy loader with singleton pattern
# ───────────────────────────────────────────────────────────────
_env_loaded = False

def load_env(force: bool = False, verbose: bool = False, auto_copy: bool = True) -> Optional[Path]:
    """
    Load environment variables from .env file.
    Uses lazy loading - only executes when called.
    
    Args:
        force: Force reload even if already loaded
        verbose: Print status messages
        auto_copy: Auto-copy .env.example to .env if missing
        
    Returns:
        Path to loaded .env file, or None if not found
    """
    global _env_loaded
    
    # Skip if already loaded (unless forced)
    if _env_loaded and not force:
        if verbose:
            print("[INFO] Environment already loaded.")
        return find_env_file(auto_copy=False)
    
    # Find or create .env file
    env_path = find_env_file(auto_copy=auto_copy, verbose=verbose)
    if not env_path:
        if verbose:
            print("[WARN] No .env or .env.example found.")
        return None
    
    # Lazy-load dotenv library
    _ensure_dotenv()
    from dotenv import load_dotenv
    
    # Load environment
    load_dotenv(dotenv_path=env_path, override=True)
    _env_loaded = True
    
    # Lazy-load yaml library
    _ensure_yaml()
    
    if verbose:
        print(f"[OK] Loaded environment: {env_path}")
    
    return env_path

# ───────────────────────────────────────────────────────────────
# [7] Value masking utilities
# ───────────────────────────────────────────────────────────────
def mask_value(val: str, show: int = 3) -> str:
    """Mask sensitive values, showing only first/last N characters."""
    if not val:
        return ""
    val = str(val)
    if len(val) <= show * 2:
        return "***"
    return f"{val[:show]}...{val[-show:]}"

_SENSITIVE_KEYS = {"KEY", "SECRET", "TOKEN", "PASSWORD", "PASS"}

def get_env_dict(mask: bool = True) -> Dict[str, str]:
    """
    Get all environment variables as dict.
    Optionally masks sensitive values.
    """
    result = {}
    for k, v in os.environ.items():
        if mask and any(s in k.upper() for s in _SENSITIVE_KEYS):
            result[k] = mask_value(v)
        else:
            result[k] = v
    return result

# ───────────────────────────────────────────────────────────────
# [8] Lazy path getters with proxy pattern
# ───────────────────────────────────────────────────────────────
_base_path_cache: Optional[Path] = None
_sys_path_cache: Optional[Path] = None

def get_base_path() -> Path:
    """
    Get project base path with lazy detection.
    Checks ENV_BASE_PATH → detect_project_root().
    """
    global _base_path_cache
    if _base_path_cache is None:
        env_base = os.getenv("ENV_BASE_PATH")
        if env_base:
            path = Path(env_base)
            if path.exists():
                _base_path_cache = path.resolve()
            else:
                _base_path_cache = detect_project_root()
        else:
            _base_path_cache = detect_project_root()
    return _base_path_cache

def get_usekit_path() -> Path:
    """
    Get USEKIT installation path.
    Always calculated as BASE_PATH / "usekit".
    """
    return get_base_path() / "usekit"

def get_sys_const_path() -> Path:
    """
    Get sys_const.yaml path.
    Always calculated as USEKIT_PATH / "sys/sys_yaml".
    """
    return get_usekit_path() / "sys" / "sys_yaml"

def get_sys_path_now() -> Path:
    """
    Get current Python execution context directory.
    Uses sys.path[0] primarily, falls back to cwd.
    """
    global _sys_path_cache
    if _sys_path_cache is None:
        try:
            p = Path(sys.path[0])
            if not str(p) or not p.exists():
                p = Path.cwd()
        except Exception:
            p = Path.cwd()
        
        if p.is_file():
            p = p.parent
        
        _sys_path_cache = p.resolve()
    
    return _sys_path_cache

# Proxy objects for lazy initialization
class _PathProxy:
    """Proxy that defers path computation until accessed."""
    def __init__(self, getter):
        self._getter = getter
        self._cache = None
    
    def _get_path(self):
        if self._cache is None:
            self._cache = self._getter()
        return self._cache
    
    def __getattr__(self, name):
        return getattr(self._get_path(), name)
    
    def __truediv__(self, other):
        return self._get_path() / other
    
    def __str__(self):
        return str(self._get_path())
    
    def __repr__(self):
        return repr(self._get_path())
    
    def __fspath__(self):
        return str(self._get_path())

BASE_PATH = _PathProxy(get_base_path)
USEKIT_PATH = _PathProxy(get_usekit_path)
SYS_CONST_PATH = _PathProxy(get_sys_const_path)
SYS_PATH_NOW = _PathProxy(get_sys_path_now)

# ───────────────────────────────────────────────────────────────
# [9] Safe path resolver
# ───────────────────────────────────────────────────────────────
def resolve_now_path(name: Optional[str] = None) -> Path:
    """
    Resolve path relative to SYS_PATH_NOW.
    Falls back to BASE_PATH if SYS_PATH_NOW is outside project.
    """
    try:
        sys_path = get_sys_path_now()
        base_path = get_base_path()
        
        # Check if sys_path is inside base_path
        sys_path.relative_to(base_path)
        
        return (sys_path / name).resolve() if name else sys_path
    except ValueError:
        # SYS_PATH_NOW is outside BASE_PATH
        base_path = get_base_path()
        return (base_path / name).resolve() if name else base_path
    except Exception as e:
        print(f"[ERROR] resolve_now_path error: {e}")
        raise

# ───────────────────────────────────────────────────────────────
# [10] Unified get_env() with caching
# ───────────────────────────────────────────────────────────────
_env_dict_cache: Optional[Dict[str, str]] = None

def get_env(mask_method: str = "mask", force_reload: bool = False) -> Dict[str, str]:
    """
    Get environment variables with optional masking.
    
    Args:
        mask_method: One of ['mask', 'ok', 'hidden']
        force_reload: Force reload from .env file
        
    Returns:
        dict: Environment variables (masked if applicable)
    """
    global _env_dict_cache
    
    # Load environment if not already loaded
    if force_reload or not _env_loaded:
        load_env(force=force_reload, verbose=False)
        _env_dict_cache = None  # Clear cache on reload
    
    # Use cached dict if available
    if _env_dict_cache is None:
        _env_dict_cache = dict(os.environ)
    
    # Apply masking
    result = {}
    for k, v in _env_dict_cache.items():
        if any(s in k.upper() for s in _SENSITIVE_KEYS):
            if mask_method == "ok":
                result[k] = "OK"
            elif mask_method == "hidden":
                result[k] = "****"
            else:
                result[k] = mask_value(v)
        else:
            result[k] = v
    
    return result

# ───────────────────────────────────────────────────────────────
# [11] sys_const.yaml loader with dynamic path injection
# ───────────────────────────────────────────────────────────────
_sys_const_cache: Optional[Dict[str, Any]] = None

def load_sys_const(force: bool = False) -> Dict[str, Any]:
    """
    Load sys_const.yaml with auto-injected BASE_PATH and USEKIT_PATH.
    
    Args:
        force: Force reload even if cached
        
    Returns:
        dict: Configuration with injected paths
    """
    global _sys_const_cache
    
    # Return cached if available
    if _sys_const_cache is not None and not force:
        return _sys_const_cache
    
    # Ensure yaml is available
    _ensure_yaml()
    import yaml
    
    # Get sys_const.yaml path
    sys_const_file = get_sys_const_path() / "sys_const.yaml"
    
    if not sys_const_file.exists():
        raise FileNotFoundError(
            f"sys_const.yaml not found at: {sys_const_file}\n"
            f"BASE_PATH: {get_base_path()}\n"
            f"USEKIT_PATH: {get_usekit_path()}"
        )
    
    # Load yaml
    with open(sys_const_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
   
    # Inject dynamic paths
    config['BASE_PATH'] = str(get_base_path())
    config['USEKIT_PATH'] = str(get_usekit_path())
    
    # Cache and return
    _sys_const_cache = config
    return config

def get_sys_const(key: Optional[str] = None, default: Any = None) -> Any:
    """
    Get value from sys_const configuration.
    
    Args:
        key: Configuration key (dot notation supported, e.g., 'MODEL.default')
        default: Default value if key not found
        
    Returns:
        Configuration value or entire config if key is None
    """
    config = load_sys_const()
    
    if key is None:
        return config
    
    # Support dot notation
    keys = key.split('.')
    value = config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value

# ───────────────────────────────────────────────────────────────
# [12] Manual .env creation helper
# ───────────────────────────────────────────────────────────────
def create_env_from_example(force: bool = False, verbose: bool = True) -> Optional[Path]:
    """
    Manually create .env from .env.example.
    
    Args:
        force: Overwrite existing .env file
        verbose: Print status messages
        
    Returns:
        Path to created .env file, or None if failed
    """
    base_path = get_base_path()
    env_file = base_path / ".env"
    example_file = base_path / ".env.example"
    
    # Check if .env already exists
    if env_file.exists() and not force:
        if verbose:
            print(f"[INFO] .env already exists: {env_file}")
            print("[INFO] Use force=True to overwrite")
        return env_file
    
    # Check if .env.example exists
    if not example_file.exists():
        if verbose:
            print(f"[ERROR] .env.example not found: {example_file}")
        return None
    
    # Copy file
    try:
        shutil.copy2(example_file, env_file)
        if verbose:
            action = "Overwritten" if force else "Created"
            print(f"[OK] {action} .env from .env.example: {env_file}")
        
        # Clear cache to reload
        global _env_file_cache, _env_loaded, _sys_const_cache
        _env_file_cache = None
        _env_loaded = False
        _sys_const_cache = None
        
        return env_file
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to copy .env.example: {e}")
        return None

# ───────────────────────────────────────────────────────────────
# [13] Debug utilities
# ───────────────────────────────────────────────────────────────
def debug_paths(verbose: bool = True) -> Dict[str, str]:
    """
    Debug utility to check all path detection.
    
    Returns:
        dict: All detected paths for inspection
    """
    info = {
        "__file__": str(Path(__file__).resolve()),
        "ENV_BASE_PATH": os.getenv("ENV_BASE_PATH", "(not set)"),
        "detected_base_path": str(get_base_path()),
        "detected_usekit_path": str(get_usekit_path()),
        "detected_sys_const_path": str(get_sys_const_path()),
        "detected_sys_path_now": str(get_sys_path_now()),
        "env_file": str(find_env_file(auto_copy=False)) if find_env_file(auto_copy=False) else "(not found)",
        "is_termux": str(is_termux()),
        "is_colab": str(is_colab()),
        "is_pip_env": str(is_pip_env()),
    }
    
    if verbose:
        print("="*80)
        print("PATH DETECTION DEBUG")
        print("="*80)
        for key, value in info.items():
            print(f"{key:25s}: {value}")
        print("="*80)
    
    return info

# ───────────────────────────────────────────────────────────────
# [14] Cache management utilities
# ───────────────────────────────────────────────────────────────
def clear_all_caches():
    """Clear all cached values (useful for testing)."""
    global _project_root_cache, _env_file_cache, _base_path_cache
    global _sys_path_cache, _env_dict_cache, _env_loaded, _sys_const_cache
    
    _project_root_cache = None
    _env_file_cache = None
    _base_path_cache = None
    _sys_path_cache = None
    _env_dict_cache = None
    _sys_const_cache = None
    _env_loaded = False
    
    # Clear function caches
    is_termux.cache_clear()
    is_colab.cache_clear()
    is_pip_env.cache_clear()

# ───────────────────────────────────────────────────────────────
# [15] Environment checks on import (Termux + Colab)
# ───────────────────────────────────────────────────────────────
def _check_termux_storage_on_import():
    """Check Termux storage permission when module is imported."""
    try:
        # Avoid circular import by importing here
        from .helper_termux_storage import warn_if_not_ready
        warn_if_not_ready()
    except ImportError:
        # helper_termux_storage not available, skip check
        pass
    except Exception:
        # Silently ignore any errors during import-time check
        pass

def _check_colab_setup_on_import():
    """Check Colab setup status when module is imported."""
    try:
        # Avoid circular import by importing here
        from .helper_colab_setup import auto_setup_on_import
        auto_setup_on_import()
    except ImportError:
        # helper_colab_setup not available, skip check
        pass
    except Exception:
        # Silently ignore any errors during import-time check
        pass

# Run environment-specific checks when module is imported
_check_termux_storage_on_import()
_check_colab_setup_on_import()

# ───────────────────────────────────────────────────────────────
# [16] Exports
# ───────────────────────────────────────────────────────────────
__all__ = [
    # Environment loading
    "load_env",
    "get_env",
    "get_env_dict",
    
    # Path getters
    "get_base_path",
    "get_usekit_path",
    "get_sys_const_path",
    "get_sys_path_now",
    "resolve_now_path",
    
    # Path proxies
    "BASE_PATH",
    "USEKIT_PATH",
    "SYS_CONST_PATH",
    "SYS_PATH_NOW",
    
    # Config loading
    "load_sys_const",
    "get_sys_const",
    
    # Utilities
    "find_env_file",
    "create_env_from_example",
    "is_termux",
    "is_colab",
    "is_pip_env",
    "clear_all_caches",
    "debug_paths",
]

# -----------------------------------------------------------------------------------------------
# [EOF] Import time: <0.001s + auto .env creation + smart path auto-binding + env checks
# -----------------------------------------------------------------------------------------------
