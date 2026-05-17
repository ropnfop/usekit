# Path: usekit.classes.data.base.post.sub.pyp.__init__.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince × ROP × FOP
# Purpose: PYP parser utilities - modularized for clarity and maintainability
# 
# Architecture:
#   extract.py  - Extraction functions (functions, classes, imports, variables)
#   format.py   - Formatting utilities (data → source code)
#   build.py    - Executable builders (for dynamic import system)
# -----------------------------------------------------------------------------------------------

from .extract import (
    PYTHON_KEYWORDS,
    DEFAULT_INDENT,
    _extract_functions,
    _extract_classes,
    _extract_imports,
    _extract_docstring,
    _extract_module_variables,
    _extract_function_dependencies,
    _extract_function_with_imports,
)

from .format import (
    _parse_signature,
    _strip_docstring,
    _format_function,
    _format_class,
    _parse_module_spec,
)

from .build import (
    _count_lines,
    _get_function_stats,
    _validate_function_exists,
    _build_executable_block,
    _build_executable_with_variables,
)


__all__ = [
    # Constants
    "PYTHON_KEYWORDS",
    "DEFAULT_INDENT",
    
    # Extraction
    "_extract_functions",
    "_extract_classes",
    "_extract_imports",
    "_extract_docstring",
    "_extract_module_variables",
    "_extract_function_dependencies",
    "_extract_function_with_imports",
    
    # Formatting
    "_parse_signature",
    "_strip_docstring",
    "_format_function",
    "_format_class",
    "_parse_module_spec",
    
    # Building
    "_count_lines",
    "_get_function_stats",
    "_validate_function_exists",
    "_build_executable_block",
    "_build_executable_with_variables",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
