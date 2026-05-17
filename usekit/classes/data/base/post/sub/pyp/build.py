# Path: usekit.classes.data.base.post.sub.pyp.build.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince × ROP × FOP
# Purpose: Build executable code blocks for dynamic import
# Features:
#   - Build executable blocks from functions/variables/classes
#   - Validation utilities
#   - Code metrics
# -----------------------------------------------------------------------------------------------

import re
from typing import Dict, List, Optional

from .extract import (
    _extract_functions,
    _extract_classes,
    _extract_imports,
    _extract_module_variables,
    _extract_function_dependencies,
)
from .format import _format_function, _format_class


# ===============================================================================
# Code Metrics
# ===============================================================================

def _count_lines(text: str, count_type: str = "all") -> int:
    """
    Count lines in text by type.
    
    Args:
        text: Text to count
        count_type: Type of lines to count:
            - "all": all lines
            - "blank": empty lines
            - "comment": comment lines
            - "code": non-blank, non-comment lines
            - "docstring": docstring lines (rough estimate)
            
    Returns:
        Number of lines
    """
    
    lines = text.splitlines()
    
    if count_type == "all":
        return len(lines)
    
    if count_type == "blank":
        return sum(1 for line in lines if not line.strip())
    
    if count_type == "comment":
        return sum(1 for line in lines if line.strip().startswith('#'))
    
    if count_type == "code":
        return len([
            line for line in lines
            if line.strip() and not line.strip().startswith('#')
        ])
    
    if count_type == "docstring":
        # Rough estimate
        in_docstring = False
        count = 0
        for line in lines:
            stripped = line.strip()
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                count += 1
            elif in_docstring:
                count += 1
        return count
    
    return 0


def _get_function_stats(func_info: Dict) -> Dict:
    """
    Calculate statistics for a function.
    
    Args:
        func_info: Function info dict from _extract_functions
        
    Returns:
        Stats dict with metrics
    """
    
    body = func_info.get("body", "")
    
    return {
        "name": func_info["name"],
        "lines_total": func_info["line_end"] - func_info["line_start"] + 1,
        "lines_code": _count_lines(body, "code"),
        "lines_blank": _count_lines(body, "blank"),
        "lines_comment": _count_lines(body, "comment"),
        "param_count": len(func_info.get("params", [])),
        "has_docstring": func_info.get("docstring") is not None,
        "is_async": func_info.get("is_async", False),
        "decorator_count": len(func_info.get("decorators", []))
    }


# ===============================================================================
# Validation
# ===============================================================================

def _validate_function_exists(text: str, func_names: List[str]) -> Dict:
    """
    Validate that functions exist in source code.
    
    Args:
        text: Python source code
        func_names: List of function names to check
        
    Returns:
        Dict with validation results:
        {
            "valid": List[str],  # functions found
            "missing": List[str]  # functions not found
        }
    """
    
    funcs = _extract_functions(text)
    existing = {f["name"] for f in funcs}
    
    valid = [name for name in func_names if name in existing]
    missing = [name for name in func_names if name not in existing]
    
    return {
        "valid": valid,
        "missing": missing
    }


# ===============================================================================
# Executable Block Builders
# ===============================================================================

def _build_executable_block(
    text: str,
    func_names: List[str],
    include_decorators: bool = True,
    include_imports: bool = True
) -> str:
    """
    Build executable code block for multiple functions.
    
    Args:
        text: Python source code
        func_names: List of function names to extract
        include_decorators: Include decorators
        include_imports: Include required imports
        
    Returns:
        Executable Python code string
    """
    
    funcs = _extract_functions(text, include_decorators=include_decorators)
    imports = _extract_imports(text) if include_imports else []
    
    # Filter requested functions
    target_funcs = [f for f in funcs if f["name"] in func_names]
    
    if not target_funcs:
        return ""
    
    parts = []
    
    # Add imports if requested
    if include_imports and imports:
        # Collect all required imports
        all_required = set()
        for func in target_funcs:
            required = _extract_function_dependencies(func, imports)
            all_required.update(required)
        
        # Add import statements
        for imp in imports:
            if imp["type"] == "from":
                if any(n in all_required for n in imp["names"]):
                    parts.append(imp["statement"])
            elif imp["type"] == "import":
                if any(n in all_required for n in imp["names"]):
                    parts.append(imp["statement"])
        
        if parts:
            parts.append("")  # blank line after imports
    
    # Add functions
    for func in target_funcs:
        parts.append(_format_function(func, include_body=True))
        parts.append("")  # blank line between functions
    
    return "\n".join(parts).rstrip()


def _build_executable_with_variables(
    text: str,
    names: List[str],
    include_decorators: bool = True,
    include_imports: bool = True
) -> str:
    """
    Build executable code block for functions and/or module variables.
    
    Intelligently detects whether each name is:
    - A function (def/async def)
    - A module-level variable
    - A class
    
    For module variables, automatically includes dependencies:
    - If variable uses a class (e.g., uw = WatchHandler()), includes the class
    - If variable uses a function, includes the function
    - Recursively resolves function dependencies
    
    Args:
        text: Python source code
        names: List of names to extract (functions, variables, or classes)
        include_decorators: Include decorators
        include_imports: Include import statements
        
    Returns:
        Executable Python code string
    """
    
    funcs = _extract_functions(text, include_decorators=include_decorators)
    classes = _extract_classes(text, include_decorators=include_decorators)
    variables = _extract_module_variables(text)
    imports = _extract_imports(text) if include_imports else []
    
    # Build lookup dicts
    func_dict = {f["name"]: f for f in funcs}
    class_dict = {c["name"]: c for c in classes}
    var_dict = {v["name"]: v for v in variables}
    
    # Track what we need to include
    needed_classes = set()
    needed_funcs = set()
    
    def find_dependencies_in_text(code_text: str, depth: int = 0):
        """Recursively find all function/class dependencies in text"""
        if depth > 10:  # Prevent infinite recursion
            return
        
        import re
        
        # Find classes referenced in text (with word boundaries)
        for cls_name in class_dict.keys():
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(cls_name) + r'\b'
            if re.search(pattern, code_text) and cls_name not in needed_classes:
                needed_classes.add(cls_name)
                # IMPORTANT: Recursively scan class methods for dependencies!
                cls_info = class_dict[cls_name]
                # Get full class source to scan for dependencies
                class_start = cls_info["line_start"]
                class_end = cls_info["line_end"]
                class_lines = text.splitlines()[class_start:class_end+1]
                class_body = '\n'.join(class_lines)
                find_dependencies_in_text(class_body, depth + 1)
        
        # Find functions referenced in text (with word boundaries)
        for func_name in func_dict.keys():
            pattern = r'\b' + re.escape(func_name) + r'\b'
            if re.search(pattern, code_text) and func_name not in needed_funcs:
                needed_funcs.add(func_name)
                # Recursively find dependencies of this function
                func_body = func_dict[func_name].get("body", "")
                func_sig = func_dict[func_name].get("signature", "")
                find_dependencies_in_text(func_sig + "\n" + func_body, depth + 1)
    
    # First pass: identify direct dependencies from requested names
    for name in names:
        if name in var_dict:
            # Check variable line for dependencies
            var_line = var_dict[name]["line"]
            find_dependencies_in_text(var_line)
        
        elif name in func_dict:
            # If requesting a function, find its dependencies too
            func_body = func_dict[name].get("body", "")
            func_sig = func_dict[name].get("signature", "")
            find_dependencies_in_text(func_sig + "\n" + func_body)
    
    # Build output
    parts = []
    found_any = False
    
    # Add imports if requested
    if include_imports and imports:
        for imp in imports:
            parts.append(imp["statement"])
        if parts:
            parts.append("")  # blank line after imports
    
    # Add needed functions (dependencies) in definition order
    # Sort by line number to maintain proper definition order
    func_items = [(fname, func_dict[fname]) for fname in needed_funcs]
    func_items.sort(key=lambda x: x[1]["line_start"])
    
    for func_name, func_info in func_items:
        parts.append(_format_function(func_info, include_body=True))
        parts.append("")
        found_any = True
    
    # Add needed classes (dependencies) in definition order
    # Sort by line number to maintain proper definition order
    class_items = [(cname, class_dict[cname]) for cname in needed_classes]
    class_items.sort(key=lambda x: x[1]["line_start"])
    
    for cls_name, cls_info in class_items:
        parts.append(_format_class_full(text, cls_info))
        parts.append("")
        found_any = True
    
    # Process each requested name (skip if already added as dependency)
    for name in names:
        if name in func_dict and name not in needed_funcs:
            # Extract function (if not already added as dependency)
            func = func_dict[name]
            parts.append(_format_function(func, include_body=True))
            parts.append("")
            found_any = True
        
        elif name in class_dict and name not in needed_classes:
            # Extract class (if not already added as dependency)
            cls = class_dict[name]
            parts.append(_format_class_full(text, cls))
            parts.append("")
            found_any = True
        
        elif name in var_dict:
            # Extract module variable
            var = var_dict[name]
            parts.append(var["line"])
            parts.append("")
            found_any = True
    
    if not found_any:
        return ""
    
    return "\n".join(parts).rstrip()


def _format_class_full(text: str, class_info: Dict) -> str:
    """
    Extract full class definition with all methods from source text.
    
    Args:
        text: Full source code
        class_info: Class info dict from _extract_classes
        
    Returns:
        Full class source code
    """
    lines = text.splitlines()
    start = class_info["line_start"]
    end = class_info["line_end"]
    
    # Extract lines from source
    class_lines = lines[start:end+1]
    
    # Join into source code
    return '\n'.join(class_lines)


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "_count_lines",
    "_get_function_stats",
    "_validate_function_exists",
    "_build_executable_block",
    "_build_executable_with_variables",
    "_format_class_full",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
