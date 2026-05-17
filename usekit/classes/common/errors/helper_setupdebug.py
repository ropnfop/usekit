# Path: usekit/classes/common/errors/
# File: helper_setupdebug.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- #
"""
Purpose: usekit, env initialization, path, sys.path, .env debug
         (conditional print based on DEBUG_OPTIONS.loader)
"""
import sys
import os
from pathlib import Path
from usekit.classes.core.env.class_env import EnvHandler
from usekit.classes.common.utils.helper_const import BASE_PATH, get_const, get_sys_path

def get_debug_option_loader():
    """
    Check the DEBUG_OPTIONS.loader flag directly.
    """
    value = get_const('DEBUG_OPTIONS.loader')
    if isinstance(value, str):
        return value.lower() in ('1', 'true', 'yes', 'on')
    return bool(value)

def print_loader_debug(env_path=None):
    """
    usekit env, path, sys.path, .env debug (conditional on DEBUG_OPTIONS.loader)
    """
    if not get_debug_option_loader():
        return

    base_path = str(BASE_PATH)
    usekit_path = str(BASE_PATH / "usekit")
    env_path = str(Path(usekit_path) / ".env")

    # --- YAML config structure (new style): use root + subkey, always relative ---
    sys_yaml_folder = get_const("SYS_PATH.yaml")        # "sys_yaml" (relative)
    sys_root = get_const("SYS_PATH.root")               # "usekit/sys" (relative)
    sys_yaml_path = str(BASE_PATH / sys_root / sys_yaml_folder / "sys_const.yaml")

    print("\n[DEBUG] --- usekit execution start ---")
    print(f"[DEBUG] __file__: {__file__}")
    print(f"[DEBUG] os.getcwd(): {os.getcwd()}")
    print(f"[DEBUG] sys.path (top 3): {sys.path[:3]}")
    print(f"[DEBUG] sys.path (full):\n  " + "\n  ".join(sys.path))
    print(f"[DEBUG] base path: {base_path}")
    print(f"[DEBUG] usekit path: {usekit_path}")
    print(f"[DEBUG] SYS_YAML_PATH: {sys_yaml_path}")

    env_path_manual = env_path
    print(f"[DEBUG] Expected .env path (manual): {env_path_manual}")
    print(f"[DEBUG] .env exists: {os.path.exists(env_path_manual)}")
    print("[DEBUG] --- usekit debug end ---\n")

# [EOF]
# ----------------------------------------------------------------------------------------------- #