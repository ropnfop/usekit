# Path: usekit.classes.common.setup.helper_setup_project
# -----------------------------------------------------------------------------------------------
# Project name and path resolution for use.setup()
# -----------------------------------------------------------------------------------------------

import os
import re
from pathlib import Path
from typing import Optional, Tuple


def _get_base_path() -> Path:
    """Resolve base path from .env or environment."""
    env_base = os.getenv("ENV_BASE_PATH")
    if env_base:
        return Path(env_base)

    # Fallback: try loader_env
    try:
        from usekit.classes.core.env.loader_env import get_base_path
        return Path(get_base_path())
    except ImportError:
        pass

    # Last resort: ~/projects/pj01
    return Path.home() / "projects" / "pj01"


def _get_default_project_name() -> str:
    """Get default project name from ENV_PROJECT or 'pj01'."""
    return os.getenv("ENV_PROJECT", "pj01")


def _project_exists(base_path: Path) -> bool:
    """Check if project directory already has usekit config."""
    return (base_path / "usekit" / "sys" / "sys_yaml").exists()


def _find_next_name(base_parent: Path, prefix: str = "pj") -> str:
    """Auto-increment project name. pj01 → pj02 → pj03 ..."""
    for i in range(1, 100):
        name = f"{prefix}{i:02d}"
        candidate = base_parent / name
        if not candidate.exists():
            return name
    return f"{prefix}99"


def _validate_project_name(name: str) -> Tuple[bool, str]:
    """Validate project name. Returns (is_valid, error_message)."""
    if not name:
        return False, "Project name cannot be empty"
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
        return False, "Name must start with letter, use only letters/digits/_/-"
    if len(name) > 50:
        return False, "Name too long (max 50 chars)"
    return True, ""


def resolve_project(verbose: bool = True) -> Optional[Tuple[str, Path]]:
    """
    Interactive project name resolution.
    
    Returns:
        (project_name, project_base_path) or None if cancelled
    """
    base_path = _get_base_path()
    default_name = _get_default_project_name()

    if verbose:
        print()
        print(f"Default project path:")
        print(f"  {base_path}")
        print()

    # Case 1: project already exists
    if _project_exists(base_path):
        print(f"Project '{default_name}' already exists at:")
        print(f"  {base_path}")
        print()

        try:
            answer = input("Overwrite existing project? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Setup cancelled")
            return None

        if answer in ("y", "yes"):
            return default_name, base_path

        # Offer new name or auto-increment
        try:
            new_name = input(
                "Enter new project name or press Enter for auto name: "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Setup cancelled")
            return None

        if new_name:
            valid, err = _validate_project_name(new_name)
            if not valid:
                print(f"[WARN] {err}")
                return None
            new_path = base_path.parent / new_name
            return new_name, new_path
        else:
            auto_name = _find_next_name(base_path.parent)
            print(f"Using next available project name: {auto_name}")
            new_path = base_path.parent / auto_name
            return auto_name, new_path

    # Case 2: project does not exist
    try:
        answer = input("Rename project? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n[INFO] Setup cancelled")
        return None

    if answer in ("y", "yes"):
        try:
            new_name = input("Enter project name: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Setup cancelled")
            return None

        valid, err = _validate_project_name(new_name)
        if not valid:
            print(f"[WARN] {err}")
            return None
        new_path = base_path.parent / new_name
        return new_name, new_path

    # Use default
    return default_name, base_path


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
