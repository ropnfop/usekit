# Path: usekit.classes.core.env.base.manager_dotenv.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- #

"""
DotEnv File Management Module for USEKIT

Handles creation, loading, and management of .env files
"""

import os
from pathlib import Path
from typing import Optional, Dict


def load_dotenv_file(
    env_path: Path,
    override: bool = True,
    verbose: bool = False
) -> bool:
    """
    Load environment variables from .env file
    
    Args:
        env_path: Path to .env file
        override: Override existing environment variables
        verbose: Print loading details
    
    Returns:
        bool: True if loaded successfully
    """
    try:
        from dotenv import load_dotenv
        
        result = load_dotenv(env_path, override=override)
        
        if verbose:
            if result:
                print(f"Loaded environment from: {env_path}")
            else:
                print(f"Failed to load environment from: {env_path}")
        
        return result
        
    except ImportError:
        if verbose:
            print("Warning: python-dotenv not installed, using manual parser")
        
        # Fallback: manual parsing
        return _load_dotenv_manual(env_path, override=override, verbose=verbose)


def _load_dotenv_manual(
    env_path: Path,
    override: bool = True,
    verbose: bool = False
) -> bool:
    """
    Manually load .env file without python-dotenv dependency
    
    Args:
        env_path: Path to .env file
        override: Override existing environment variables
        verbose: Print loading details
    
    Returns:
        bool: True if loaded successfully
    """
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' not in line:
                    if verbose:
                        print(f"Warning: Invalid line {line_num} in .env: {line}")
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Set environment variable
                if override or key not in os.environ:
                    os.environ[key] = value
        
        if verbose:
            print(f"Manually loaded environment from: {env_path}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"Error loading .env file: {e}")
        return False


def create_env_template(
    target_path: Path,
    base_path: Optional[Path] = None,
    overwrite: bool = False,
    verbose: bool = False
) -> bool:
    """
    Create a .env template file
    
    Args:
        target_path: Where to create the .env file
        base_path: Base path to include in template
        overwrite: Overwrite existing file
        verbose: Print creation details
    
    Returns:
        bool: True if created successfully
    """
    if target_path.exists() and not overwrite:
        if verbose:
            print(f".env file already exists: {target_path}")
        return False
    
    # Determine base path
    if base_path is None:
        base_path = target_path.parent
    
    # Create template content
    template = f"""# USEKIT Environment Configuration
# Generated automatically - customize as needed

# Base path for project
ENV_BASE_PATH={base_path}

# Add your custom environment variables below
# Example:
# DATABASE_URL=sqlite:///data.db
# API_KEY=your_api_key_here
"""
    
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(template, encoding='utf-8')
        
        if verbose:
            print(f"Created .env template: {target_path}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"Error creating .env template: {e}")
        return False


def parse_dotenv(env_path: Path) -> Dict[str, str]:
    """
    Parse .env file and return key-value pairs
    
    Args:
        env_path: Path to .env file
    
    Returns:
        Dict[str, str]: Dictionary of environment variables
    """
    env_vars = {}
    
    try:
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
                    value = value.strip()
                    
                    # Remove quotes
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    env_vars[key] = value
    
    except Exception:
        pass
    
    return env_vars


def update_env_variable(
    env_path: Path,
    key: str,
    value: str,
    create_if_missing: bool = True
) -> bool:
    """
    Update or add a variable in .env file
    
    Args:
        env_path: Path to .env file
        key: Variable name
        value: Variable value
        create_if_missing: Create file if it doesn't exist
    
    Returns:
        bool: True if updated successfully
    """
    if not env_path.exists():
        if create_if_missing:
            create_env_template(env_path)
        else:
            return False
    
    try:
        # Read existing content
        lines = []
        key_found = False
        
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Update or add key
        new_lines = []
        for line in lines:
            stripped = line.strip()
            
            # Check if this line contains our key
            if '=' in stripped and not stripped.startswith('#'):
                line_key = stripped.split('=', 1)[0].strip()
                if line_key == key:
                    new_lines.append(f"{key}={value}\n")
                    key_found = True
                    continue
            
            new_lines.append(line)
        
        # Add key if not found
        if not key_found:
            new_lines.append(f"\n{key}={value}\n")
        
        # Write back
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        return True
        
    except Exception:
        return False


def remove_env_variable(env_path: Path, key: str) -> bool:
    """
    Remove a variable from .env file
    
    Args:
        env_path: Path to .env file
        key: Variable name to remove
    
    Returns:
        bool: True if removed successfully
    """
    if not env_path.exists():
        return False
    
    try:
        # Read existing content
        lines = []
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Filter out the key
        new_lines = []
        for line in lines:
            stripped = line.strip()
            
            # Check if this line contains our key
            if '=' in stripped and not stripped.startswith('#'):
                line_key = stripped.split('=', 1)[0].strip()
                if line_key == key:
                    continue  # Skip this line
            
            new_lines.append(line)
        
        # Write back
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        return True
        
    except Exception:
        return False


def validate_env_file(env_path: Path) -> tuple[bool, list[str]]:
    """
    Validate .env file format and required variables
    
    Args:
        env_path: Path to .env file
    
    Returns:
        tuple[bool, list[str]]: (is_valid, list of issues)
    """
    issues = []
    
    if not env_path.exists():
        issues.append(f"File not found: {env_path}")
        return False, issues
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                stripped = line.strip()
                
                # Skip comments and empty lines
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Check format
                if '=' not in stripped:
                    issues.append(f"Line {line_num}: Invalid format (missing '=')")
                    continue
                
                key, value = stripped.split('=', 1)
                key = key.strip()
                
                # Validate key
                if not key:
                    issues.append(f"Line {line_num}: Empty key")
                
                if not key.replace('_', '').isalnum():
                    issues.append(f"Line {line_num}: Invalid key format (use A-Z, 0-9, _)")
    
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return len(issues) == 0, issues
