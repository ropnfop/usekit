# Path: usekit.classes.common.setup.helper_setup_config
# -----------------------------------------------------------------------------------------------
# Config writing and editor options for use.setup()
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


# Default editor config
_EDITOR_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 7979,
    "auto_bash": False,
    "autostart": False,
}


def ask_editor_options(verbose: bool = True) -> Dict:
    """
    Ask user for editor behavior settings.
    
    Returns:
        dict with host, port, auto_bash, autostart keys
    """
    config = _EDITOR_DEFAULTS.copy()

    if verbose:
        print()

    try:
        answer = input("Enable auto bash command handling? [y/N]: ").strip().lower()
        config["auto_bash"] = answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        pass

    status = "enabled" if config["auto_bash"] else "disabled"
    if verbose:
        print(f"Auto bash handling {status}.")

    try:
        answer = input("Auto-start editor on Termux launch? [y/N]: ").strip().lower()
        config["autostart"] = answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        pass

    status = "enabled" if config["autostart"] else "disabled"
    if verbose:
        print(f"Editor autostart {status}.")

    return config


def create_project_structure(project_path: Path, verbose: bool = True) -> bool:
    """
    Create project directory structure.
    
    Creates:
        project_path/
          usekit/
            sys/
              sys_yaml/
            .env
          _tmp/
          data/
    """
    dirs = [
        project_path / "usekit" / "sys" / "sys_yaml",
        project_path / "usekit" / "sys" / "sys_json",
        project_path / "usekit" / "sys" / "sys_km",
        project_path / "_tmp",
        project_path / "data",
    ]

    try:
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        if verbose:
            print()
            print("Creating project structure...")
            print()
            print(f"  {project_path.name}/")
            print(f"    usekit/")
            print(f"      sys/")
            print(f"        sys_yaml/")
            print(f"    _tmp/")
            print(f"    data/")

        return True
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to create directories: {e}")
        return False


def build_sys_project_data(
    project_name: str,
    editor_config: Dict,
) -> Dict:
    """Build the sys_project.yaml data dict."""
    today = datetime.now().strftime("%Y-%m-%d")

    return {
        "project": {
            "name": project_name,
        },
        "editor": {
            "host": editor_config.get("host", _EDITOR_DEFAULTS["host"]),
            "port": editor_config.get("port", _EDITOR_DEFAULTS["port"]),
            "auto_bash": editor_config.get("auto_bash", _EDITOR_DEFAULTS["auto_bash"]),
        },
        "created": today,
        "updated": today,
    }


def write_sys_project(
    project_path: Path,
    data: Dict,
    verbose: bool = True,
) -> bool:
    """
    Write sys_project.yaml to project's sys_yaml folder.
    Also updates the central cache via helper_const.
    """
    yaml_dir = project_path / "usekit" / "sys" / "sys_yaml"
    yaml_path = yaml_dir / "sys_project.yaml"

    try:
        import yaml

        yaml_dir.mkdir(parents=True, exist_ok=True)
        with yaml_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                data, f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        if verbose:
            print()
            print(f"Config saved:")
            print(f"  {yaml_path}")

        # Update central cache
        try:
            from usekit.classes.common.utils.helper_const import (
                save_sys_project,
                clear_sys_project_cache,
            )
            clear_sys_project_cache()
            save_sys_project(data)
        except ImportError:
            pass

        return True

    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to write config: {e}")
        return False


def _find_source_usekit() -> Path:
    """Find the source usekit package directory (where .env.example lives)."""
    import usekit
    return Path(usekit.__file__).parent


def copy_source_configs(project_path: Path, project_name: str, verbose: bool = True) -> bool:
    """
    Copy .env.example → .env (with path update) and sys_const.yaml from source.
    Skips files that already exist in target.
    """
    source = _find_source_usekit()
    success = True

    # ── .env.example → .env ──
    env_src = source / ".env.example"
    env_dst = project_path / "usekit" / ".env"

    if env_dst.exists():
        if verbose:
            print(f"  .env already exists, skipping.")
    elif env_src.exists():
        try:
            content = env_src.read_text(encoding="utf-8")
            # Update ENV_BASE_PATH to new project path
            content = content.replace(
                "# ENV_BASE_PATH=/path/to/your/project",
                f"ENV_BASE_PATH={project_path}",
            )
            # Also handle uncommented line if present
            import re
            content = re.sub(
                r'^ENV_BASE_PATH=.*$',
                f'ENV_BASE_PATH={project_path}',
                content,
                flags=re.MULTILINE,
            )
            # Ensure ENV_BASE_PATH is set (if no match found, append)
            if f"ENV_BASE_PATH={project_path}" not in content:
                content += f"\nENV_BASE_PATH={project_path}\n"

            env_dst.write_text(content, encoding="utf-8")
            if verbose:
                print(f"  Copied: .env.example → .env")
        except Exception as e:
            if verbose:
                print(f"  [WARN] .env copy failed: {e}")
            success = False
    else:
        # Fallback: create minimal .env
        try:
            content = (
                f"# USEKIT environment config\n"
                f"# Generated by use.setup()\n"
                f"\n"
                f"ENV_BASE_PATH={project_path}\n"
                f"ENV_PROJECT={project_name}\n"
            )
            env_dst.write_text(content, encoding="utf-8")
            if verbose:
                print(f"  Created: .env (minimal)")
        except Exception as e:
            if verbose:
                print(f"  [WARN] .env creation failed: {e}")
            success = False

    # ── sys_const.yaml ──
    const_src = source / "sys" / "sys_yaml" / "sys_const.yaml"
    const_dst = project_path / "usekit" / "sys" / "sys_yaml" / "sys_const.yaml"

    if const_dst.exists():
        if verbose:
            print(f"  sys_const.yaml already exists, skipping.")
    elif const_src.exists():
        try:
            import shutil
            const_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(const_src), str(const_dst))
            if verbose:
                print(f"  Copied: sys_const.yaml")
        except Exception as e:
            if verbose:
                print(f"  [WARN] sys_const.yaml copy failed: {e}")
            success = False
    else:
        if verbose:
            print(f"  [WARN] sys_const.yaml source not found at {const_src}")
        success = False

    return success


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
