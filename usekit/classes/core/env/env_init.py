# Path: usekit.classes.core.env.env_init.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- #

"""
USEKIT Environment Module

Clean API for environment detection, path resolution, and .env management.
"""

from usekit.classes.core.env.loader_env import (
    # Main functions
    load_env,
    get_base_path,
    set_base_path,
    reset_env,
    get_env_info,
    quick_setup,
    get_usekit_path,
)

from usekit.classes.core.env.base.detector_env import (
    detect_environment,
    get_default_paths,
    suggest_base_path,
    is_pip_installed,
    get_environment_info,
)

from usekit.classes.core.env.base.resolver_path import (
    find_project_root,
    find_env_file_path,
    resolve_base_path_priority,
    normalize_path,
)

from usekit.classes.core.env.base.manager_dotenv import (
    load_dotenv_file,
    create_env_template,
    parse_dotenv,
    update_env_variable,
    remove_env_variable,
    validate_env_file,
)


__all__ = [
    # Main API (most commonly used)
    'load_env',
    'get_base_path',
    'set_base_path',
    'quick_setup',
    
    # Environment detection
    'detect_environment',
    'get_env_info',
    
    # Path resolution
    'find_project_root',
    'normalize_path',
    
    # DotEnv management
    'create_env_template',
    'parse_dotenv',
    'update_env_variable',
]
