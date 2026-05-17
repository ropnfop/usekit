# Path: usekit.classes.data.base.post.sub.parser_pyp_sub.py
# -----------------------------------------------------------------------------------------------
# BACKWARDS COMPATIBILITY LAYER
# 
# This file maintains compatibility with existing imports while the codebase
# has been refactored into a modular structure under pyp/
#
# Old import (still works):
#   from usekit.classes.data.base.post.sub.parser_pyp_sub import _extract_functions
#
# New import (recommended):
#   from usekit.classes.data.base.post.sub.pyp import _extract_functions
#
# This compatibility layer will be maintained for backwards compatibility.
# -----------------------------------------------------------------------------------------------

# Re-export everything from new modular structure
from .pyp import (
    # Constants
    PYTHON_KEYWORDS,
    DEFAULT_INDENT,
    
    # Extraction functions (from pyp.extract)
    _extract_functions,
    _extract_classes,
    _extract_imports,
    _extract_docstring,
    _extract_module_variables,
    _extract_function_dependencies,
    _extract_function_with_imports,
    
    # Formatting functions (from pyp.format)
    _parse_signature,
    _strip_docstring,
    _format_function,
    _format_class,
    _parse_module_spec,
    
    # Build functions (from pyp.build)
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
