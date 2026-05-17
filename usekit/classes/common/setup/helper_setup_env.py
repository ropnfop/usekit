# Path: usekit.classes.common.setup.helper_setup_env
# -----------------------------------------------------------------------------------------------
# Environment detection and dependency check for use.setup()
# -----------------------------------------------------------------------------------------------

import sys
import platform
from typing import Dict, List, Tuple


# Core packages (must be installed via pyproject.toml)
CORE_DEPS = ["yaml", "dotenv"]

# Optional packages (notice only, never auto-installed)
OPTIONAL_DEPS = ["requests"]

# Import name → display name mapping
_DISPLAY_NAMES = {
    "yaml": "PyYAML",
    "dotenv": "python-dotenv",
    "requests": "requests",
}


def _detect_platform() -> str:
    """Detect current platform. Returns 'termux', 'colab', or 'local'."""
    try:
        from usekit.classes.core.env.loader_env import is_termux, is_colab
        if is_termux():
            return "termux"
        if is_colab():
            return "colab"
    except ImportError:
        pass
    return "local"


def _check_import(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _check_dependencies() -> Tuple[Dict[str, bool], Dict[str, bool]]:
    """Check core and optional dependencies. Returns (core, optional) dicts."""
    core = {name: _check_import(name) for name in CORE_DEPS}
    optional = {name: _check_import(name) for name in OPTIONAL_DEPS}
    return core, optional


def detect_environment(verbose: bool = True) -> Dict:
    """
    Detect and display system environment info.
    
    Returns:
        dict with platform, python, cwd keys
    """
    import os

    env = {
        "platform": _detect_platform(),
        "python": platform.python_version(),
        "cwd": os.getcwd(),
    }

    if verbose:
        print()
        print("=" * 60)
        print("[USEKIT SETUP]")
        print("=" * 60)
        print()
        print("System environment:")
        print(f"  - Platform : {env['platform'].capitalize()}")
        print(f"  - Python   : {env['python']}")
        print(f"  - Current  : {env['cwd']}")

    return env


def check_dependencies(verbose: bool = True) -> Tuple[Dict[str, bool], Dict[str, bool]]:
    """
    Check and display dependency status.
    
    Returns:
        (core_results, optional_results) tuple
    """
    core, optional = _check_dependencies()

    if verbose:
        print()
        print("[USEKIT DEPENDENCIES]")
        print()
        print("Core:")
        for name, ok in core.items():
            display = _DISPLAY_NAMES.get(name, name)
            status = "OK" if ok else "MISSING"
            print(f"  {display:<18}: {status}")

        print()
        print("Optional:")
        for name, ok in optional.items():
            display = _DISPLAY_NAMES.get(name, name)
            status = "OK" if ok else "not installed"
            print(f"  {display:<18}: {status}")

        # Warn if core deps missing
        missing = [n for n, ok in core.items() if not ok]
        if missing:
            print()
            names = ", ".join(_DISPLAY_NAMES.get(m, m) for m in missing)
            print(f"  [WARN] Missing core: {names}")
            print(f"  Fix: pip install {' '.join(names)}")
        else:
            print()
            print("Optional packages can be installed separately as needed.")

    return core, optional


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
