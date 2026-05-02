# Path: usekit.classes.common.utils.helper_format.py
# -----------------------------------------------------------------------------------------------
#  Parser Factory - Format-based Info
#  Created by: THE Little Prince × ROP × FOP'
# -----------------------------------------------------------------------------------------------

import importlib
from functools import lru_cache
from typing import Optional, Set, List, Union

# ===============================================================================
# Exceptions
# ===============================================================================

class ParserLoadError(Exception):
    """Raised when parser module cannot be loaded"""
    pass


# ===============================================================================
# Format Classification
# ===============================================================================

# TXT-compatible formats (share TxtParser)
TXT_FORMATS: Set[str] = {
    # Plain text
    "txt",
    
    # Markup & Documentation
    "md", "markdown",
    "rst", "restructuredtext",
    
    # SQL & Database
    "sql", "ddl", "dml",
    
    # Configuration
    "ini", "conf", "config",
    "env", "dotenv",
    
    # Logs
    "log", "logs",
    
    # Km
    "km", "kms",
    
    # Scripts
    "sh", "bash",
    "dockerfile",
    
    # Version Control
    "gitignore", "dockerignore",
    
    # Other text-based
    "properties",
    "cfg", 
    
    # Other text-based-etc
    "all", "any",
}

# Structured data formats (have dedicated parsers)
STRUCTURED_FORMATS: Set[str] = {
    "json",
    "yaml", "yml",
    "csv", "tsv",
    "xml",
    "toml",  # Advanced structured format
}

# Code formats (need AST/special handling)
CODE_FORMATS: Set[str] = {
    "pyp", "py", "python",
    "js", "javascript",
}

# Binary formats (special handling)
BINARY_FORMATS: Set[str] = {
    "pickle", "pkl",
}

# All supported formats
ALL_FORMATS: Set[str] = TXT_FORMATS | STRUCTURED_FORMATS | CODE_FORMATS | BINARY_FORMATS


# ===============================================================================
# Format Normalization
# ===============================================================================

FORMAT_ALIASES = {
    # Markdown
    "markdown": "md",
    "restructuredtext": "rst",
    
    # Python
    "python": "py",
    "pyp": "py",
    
    # JavaScript
    "javascript": "js",
    
    # YAML
    "yml": "yaml",
    
    # Config
    "config": "conf",
    "dotenv": "env",
    
    # Logs
    "logs": "log",
    
    # Kms
    "kms": "km",
    
    # Binary
    "pickle": "pkl",
}


def _normalize(fmt: str) -> str:
    """Normalize format string (lowercase, strip, resolve aliases)"""
    normalized = (fmt or "").strip().lower()
    return FORMAT_ALIASES.get(normalized, normalized)

# ===============================================================================
#  Format Wrapper
# ===============================================================================

FMT_MAP = {
    # ───────────────────────────────
    # TEXT & DOC
    # ───────────────────────────────
    "txt": ".txt",
    "log": ".log",
    "log": ".log",
    "km": ".km",
    "md": ".md",
    "markdown": ".md",
    "rst": ".rst",
    "restructuredtext": ".rst",
    "cfg": ".cfg",
    "conf": ".conf",
    "config": ".conf",
    "env": ".env",
    "dotenv": ".env",
    "properties": ".properties",

    # ───────────────────────────────
    # DATA
    # ───────────────────────────────
    "json": ".json",
    "yaml": ".yaml",
    "yml": ".yaml",
    "csv": ".csv",
    "tsv": ".tsv",
    "xml": ".xml",

    # ───────────────────────────────
    # CODE
    # ───────────────────────────────
    "python": ".py",
    "py": ".py",
    "pyp": ".py",
    "javascript": ".js",
    "js": ".js",
    "sh": ".sh",
    "bash": ".sh",

    # ───────────────────────────────
    # DB / DDL
    # ───────────────────────────────
    "sql": ".sql",
    "ddl": ".sql",
    "dml": ".sql",

    # ───────────────────────────────
    # BINARY
    # ───────────────────────────────
    "pickle": ".pkl",
    "pkl": ".pkl",

    # ───────────────────────────────
    # SPECIAL (none)
    # ───────────────────────────────
    "dockerfile": "",
    "gitignore": "",
    "dockerignore": "",
    
    # ───────────────────────────────
    # DEFAULT
    # ───────────────────────────────
    "all": ".log",
    "any": ".log",
}

# ===============================================================================
#  Parser format Wrapper
# ===============================================================================

PARSER_MAP = {
    # ───────────────────────────────
    # TEXT & DOC ANY
    # ───────────────────────────────
    "txt": "txt",
    "ini": "txt",
    "log": "txt",
    "logs": "txt",
    "km": "txt",
    "rst": "txt",
    "restructuredtext": "txt",
    "cfg": "txt",
    "conf": "txt",
    "config": "txt",
    "env": "txt",
    "dotenv": "txt",
    "properties": "txt",
    "xml": "txt",     
    "toml": "txt",
    "javascript": "txt",
    "js": "txt",
    "sh": "txt",
    "bash": "txt",
    
    # ───────────────────────────────
    # DEFAULT
    # ───────────────────────────────
    "all": "txt",
    "any": "txt",

    # ───────────────────────────────
    # SPECIAL (none)
    # ───────────────────────────────
    "dockerfile": "txt",
    "gitignore": "txt",
    "dockerignore": "txt",
    
    # ───────────────────────────────
    # DATA
    # ───────────────────────────────
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "csv": "csv",
    "tsv": "csv",
    "md": "md",
    "markdown": "md",

    # ───────────────────────────────
    # CODE
    # ───────────────────────────────
    "python": "pyp",
    "py": "pyp",
    "pyp": "pyp",

    # ───────────────────────────────
    # DB / DDL
    # ───────────────────────────────
    "sql": "sql",
    "dml": "sql",
    "ddl": "ddl",

    # ───────────────────────────────
    # BINARY
    # ───────────────────────────────
    "pickle": "pkl",
    "pkl": "pkl",

}

# ===============================================================================
# Utility Functions
# ===============================================================================

def get_supported_formats() -> Set[str]:
    """Get set of all supported format names"""
    return ALL_FORMATS.copy()


def is_txt_compatible(fmt: str) -> bool:
    """Check if format is TXT-compatible (shares TxtParser)"""
    return _normalize(fmt) in TXT_FORMATS


def is_structured_format(fmt: str) -> bool:
    """Check if format is structured data (JSON/YAML/CSV/...)"""
    return _normalize(fmt) in STRUCTURED_FORMATS


def is_code_format(fmt: str) -> bool:
    """Check if format is code (Python/JS/...)"""
    return _normalize(fmt) in CODE_FORMATS


def is_binary_format(fmt: str) -> bool:
    """Check if format is binary (pickle/...)"""
    return _normalize(fmt) in BINARY_FORMATS


def get_format_category(fmt: str) -> str:
    """
    Get category of format.
    
    Returns:
        "txt" | "structured" | "code" | "binary" | "unknown"
    """
    key = _normalize(fmt)
    
    if key in TXT_FORMATS:
        return "txt"
    elif key in STRUCTURED_FORMATS:
        return "structured"
    elif key in CODE_FORMATS:
        return "code"
    elif key in BINARY_FORMATS:
        return "binary"
    else:
        return "unknown"

def get_format_set(fmt: str) -> str:
    """
    Get file extension for a given format.
    
    Args:
        fmt: Format name (e.g., "json", "yaml", "txt")
        
    Returns:
        File extension with leading dot (e.g., ".json", ".yaml")
        
    Raises:
        ParserLoadError: If format is not supported
        
    Example:
        get_format_set("json")  # → ".json"
        get_format_set("yaml")  # → ".yaml"
        get_format_set("py")    # → ".py"
    """
    key = _normalize(fmt)
    
    # Validate format
    if key not in ALL_FORMATS:
        raise ParserLoadError(
            f"[Parser] Unknown format: '{fmt}' (normalized: '{key}')\n"
            f"Supported formats: {sorted(ALL_FORMATS)}"
        )
        
    fmt_lower = (fmt or "").lower().strip()
    return FMT_MAP.get(fmt_lower, f".{fmt_lower}")

def get_format_parser(fmt: str) -> str:
    """
    Get file extension for a given format.    
    Args:
        fmt: Format name (e.g., "json", "yaml", "txt")     
    Returns:
        File extension with leading dot (e.g., ".json", ".yaml")    
    Raises:
        ParserLoadError: If format is not supported        
    Example:
        get_format_parser("json")  # → "json"
        get_format_parser("log")  # → "txt"
        get_format_parser("py")    # → "pyp"
    """
    key = _normalize(fmt)
    
    # Validate format
    if key not in ALL_FORMATS:
        raise ParserLoadError(
            f"[Parser] Unknown format: '{fmt}' (normalized: '{key}')\n"
            f"Supported formats: {sorted(ALL_FORMATS)}"
        )
        
    fmt_lower = (fmt or "").lower().strip()
    return PARSER_MAP.get(fmt_lower, f".{fmt_lower}")

def get_extension_from_file(filepath: Union[str, 'Path']) -> Optional[str]:
    """
    Detect format type from file extension.
    
    Args:
        filepath: File path or filename
        
    Returns:
        Format type string (e.g., "json", "yaml", "txt") or None if unknown
        
    Example:
        get_extension_from_file("config.json")  # → "json"
        get_extension_from_file("/data/log.txt")  # → "txt"
        get_extension_from_file("data.unknown")  # → None
    """
    try:
        from pathlib import Path
        path = Path(filepath)
        ext = path.suffix.lower()
        
        if not ext:
            return None
        
        # Reverse lookup: extension → format
        EXT_TO_FORMAT = {
            # Text & Documentation
            ".txt": "txt",
            ".log": "log",
            ".km": "km",
            ".md": "md",
            ".markdown": "md",
            ".rst": "rst",
            
            # Structured Data
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".csv": "csv",
            ".tsv": "tsv",
            ".xml": "xml",
            ".toml": "toml",
            
            # Code
            ".py": "pyp",
            ".pyp": "pyp",
            ".js": "js",
            ".sh": "sh",
            
            # Configuration
            ".ini": "ini",
            ".conf": "conf",
            ".config": "conf",
            ".env": "env",
            ".properties": "properties",
            ".cfg": "cfg",
            
            # Database
            ".sql": "sql",
            ".ddl": "ddl",
            ".dml": "dml",
            
            # Binary
            ".pkl": "pkl",
            ".pickle": "pkl",
        }
        
        return EXT_TO_FORMAT.get(ext)
    except Exception:
        return None


def get_all_extensions() -> List[str]:
    """
    Get all supported file extensions.
    
    Returns:
        List of all unique extensions
        
    Example:
        get_all_extensions()  # → [".json", ".yaml", ".txt", ...]
    """
    return sorted(set(FMT_MAP.values()))

 
# ===============================================================================
# Export
# ===============================================================================