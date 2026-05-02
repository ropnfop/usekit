# Path: usekit.classes.data.base.post.sub.pyp.format.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince × ROP × FOP
# Purpose: Python source code formatting and parsing utilities
# Features:
#   - Function/class formatting (data → source code)
#   - Signature parsing
#   - Docstring manipulation
#   - Module spec parsing
# -----------------------------------------------------------------------------------------------

import re
from typing import Dict, List, Optional, Tuple

from .extract import DEFAULT_INDENT


# ===============================================================================
# Signature Parsing
# ===============================================================================

def _parse_signature(signature: str) -> Tuple[List[str], Optional[str]]:
    """
    Parse function signature to extract parameters and return type.
    
    Args:
        signature: Function signature string
        
    Returns:
        (parameter_names, return_type)
    """
    
    # Extract parameters
    params = []
    paren_start = signature.find('(')
    paren_end = signature.rfind(')')
    
    if paren_start >= 0 and paren_end > paren_start:
        params_str = signature[paren_start+1:paren_end]
        
        # Split by comma (simple parsing, doesn't handle nested defaults)
        if params_str.strip():
            for param in params_str.split(','):
                param = param.strip()
                if not param:
                    continue
                
                # Remove default value
                if '=' in param:
                    param = param[:param.index('=')].strip()
                
                # Remove type hint
                if ':' in param:
                    param = param[:param.index(':')].strip()
                
                # Skip *args, **kwargs markers
                param = param.lstrip('*')
                
                if param and param not in ('self', 'cls'):
                    params.append(param)
    
    # Extract return type
    returns = None
    arrow_idx = signature.find('->')
    if arrow_idx >= 0:
        returns = signature[arrow_idx+2:].split(':')[0].strip()
    
    return params, returns


# ===============================================================================
# Docstring Utilities
# ===============================================================================

def _strip_docstring(body: str) -> str:
    """
    Remove docstring from function/class body.
    
    Args:
        body: Function or class body text
        
    Returns:
        Body with docstring removed
    """
    
    lines = body.splitlines()
    if not lines:
        return body
    
    first_line = lines[0].strip()
    
    # Check for docstring
    if not (first_line.startswith('"""') or first_line.startswith("'''")):
        return body
    
    quote = '"""' if first_line.startswith('"""') else "'''"
    
    # Single line docstring
    if first_line.count(quote) >= 2:
        return '\n'.join(lines[1:])
    
    # Multi-line docstring - find closing quote
    for i, line in enumerate(lines[1:], 1):
        if quote in line:
            return '\n'.join(lines[i+1:])
    
    return body


# ===============================================================================
# Function/Class Formatting
# ===============================================================================

def _format_function(func_info: Dict, include_body: bool = True) -> str:
    """
    Format function info back to source code.
    
    Args:
        func_info: Function info dict
        include_body: Include function body
        
    Returns:
        Formatted source code
    """
    
    parts = []
    base_indent = func_info.get("indent", 0)
    
    # Dedent helper - removes base indentation from extracted code
    def dedent_line(line: str, indent_to_remove: int) -> str:
        """Remove specified number of leading spaces from line"""
        if not line.strip():  # preserve blank lines
            return line
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces >= indent_to_remove:
            return line[indent_to_remove:]
        return line
    
    # Add decorators (dedented if needed)
    if func_info.get("decorators"):
        if base_indent > 0:
            parts.extend([dedent_line(dec, base_indent) for dec in func_info["decorators"]])
        else:
            parts.extend(func_info["decorators"])
    
    # Add signature (dedented if needed)
    signature = func_info["signature"]
    if base_indent > 0:
        # For multiline signatures, dedent each line
        sig_lines = signature.split('\n')
        signature = '\n'.join(dedent_line(line, base_indent) for line in sig_lines)
    parts.append(signature)
    
    # Add docstring (with proper indentation - always 4 spaces from def level)
    if include_body and func_info.get("docstring"):
        indent_str = " " * DEFAULT_INDENT
        parts.append(f'{indent_str}"""{func_info["docstring"]}"""')
    
    # Add body (dedented if needed)
    if include_body and func_info.get("body"):
        body = func_info["body"]
        if base_indent > 0:
            # Dedent each line in body
            body_lines = body.split('\n')
            body = '\n'.join(dedent_line(line, base_indent) for line in body_lines)
        parts.append(body)
    
    return '\n'.join(parts)


def _format_class(class_info: Dict, include_methods: bool = True) -> str:
    """
    Format class info back to source code.
    
    Args:
        class_info: Class info dict
        include_methods: Include method bodies (not implemented)
        
    Returns:
        Formatted source code
    """
    
    parts = []
    
    # Add decorators
    if class_info.get("decorators"):
        parts.extend(class_info["decorators"])
    
    # Add signature
    parts.append(class_info["signature"])
    
    # Add docstring
    if class_info.get("docstring"):
        indent = " " * (class_info.get("indent", 0) + DEFAULT_INDENT)
        parts.append(f'{indent}"""{class_info["docstring"]}"""')
    
    return '\n'.join(parts)


# ===============================================================================
# Module Spec Parsing
# ===============================================================================

def _parse_module_spec(spec: str) -> Dict:
    """
    Parse module specification string.
    
    Formats:
        "module_name"                 → module only
        "module_name:func1,func2"     → module + functions
        "module_name:*"               → module + all
    
    Args:
        spec: Module specification string
        
    Returns:
        Dict with parsed components:
        {
            "module": str,
            "functions": List[str] | None,
            "import_all": bool
        }
    """
    
    if ':' not in spec:
        return {
            "module": spec.strip(),
            "functions": None,
            "import_all": False
        }
    
    parts = spec.split(':', 1)
    module = parts[0].strip()
    func_part = parts[1].strip()
    
    if func_part == '*':
        return {
            "module": module,
            "functions": None,
            "import_all": True
        }
    
    functions = [f.strip() for f in func_part.split(',')]
    
    return {
        "module": module,
        "functions": functions,
        "import_all": False
    }


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "_parse_signature",
    "_strip_docstring",
    "_format_function",
    "_format_class",
    "_parse_module_spec",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
