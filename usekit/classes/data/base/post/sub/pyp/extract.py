# Path: usekit.classes.data.base.post.sub.pyp.extract.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince × ROP × FOP
# Purpose: Python source code extraction utilities
# Features:
#   - Function extraction: def/async def with decorators
#   - Class extraction: class with methods
#   - Import extraction: from/import statements
#   - Docstring extraction
#   - Module variable extraction
#   - Dependency analysis
# -----------------------------------------------------------------------------------------------

import re
from typing import Dict, List, Optional, Tuple


# ===============================================================================
# Constants
# ===============================================================================

PYTHON_KEYWORDS = {
    "def", "class", "import", "from", "async", "await",
    "if", "elif", "else", "for", "while", "try", "except", "finally",
    "with", "return", "yield", "lambda", "pass", "break", "continue"
}

DEFAULT_INDENT = 4


# ===============================================================================
# Function Extraction
# ===============================================================================

def _extract_functions(
    text: str,
    include_async: bool = True,
    include_decorators: bool = True,
    include_docstring: bool = True,
    include_body: bool = True
) -> List[Dict]:
    """
    Extract all function definitions from Python source.
    
    Args:
        text: Python source code
        include_async: Include async functions
        include_decorators: Include decorator lines
        include_docstring: Include docstring in body
        include_body: Include function body
        
    Returns:
        List of function info dicts:
        {
            "name": str,
            "signature": str,
            "decorators": List[str],
            "docstring": str,
            "body": str,
            "line_start": int,
            "line_end": int,
            "indent": int,
            "is_async": bool,
            "params": List[str],
            "returns": Optional[str]
        }
    """
    
    lines = text.splitlines()
    functions = []
    
    # Patterns
    def_pattern = re.compile(r'^(\s*)(async\s+)?def\s+(\w+)\s*\(')
    decorator_pattern = re.compile(r'^(\s*)@')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Collect decorators
        decorators = []
        decorator_indent = None
        while i < len(lines) and decorator_pattern.match(lines[i]):
            dec_line = lines[i]
            if decorator_indent is None:
                decorator_indent = len(dec_line) - len(dec_line.lstrip())
            decorators.append(dec_line)
            i += 1
        
        if i >= len(lines):
            break
        
        line = lines[i]
        
        # Match function definition
        def_match = def_pattern.match(line)
        if not def_match:
            i += 1
            continue
        
        indent_str = def_match.group(1)
        indent = len(indent_str)
        is_async = def_match.group(2) is not None
        func_name = def_match.group(3)
        
        # Skip async if not requested
        if is_async and not include_async:
            i += 1
            continue
        
        # Extract full signature (may span multiple lines)
        sig_lines = []
        sig_start = i
        paren_count = 0
        found_colon = False
        
        while i < len(lines):
            curr_line = lines[i]
            sig_lines.append(curr_line)
            
            # Count parentheses
            paren_count += curr_line.count('(') - curr_line.count(')')
            
            # Check for closing
            if paren_count == 0 and ':' in curr_line:
                found_colon = True
                break
            
            i += 1
        
        if not found_colon:
            i += 1
            continue
        
        signature = '\n'.join(sig_lines)
        
        # Extract parameters and return type
        from .format import _parse_signature
        params, returns = _parse_signature(signature)
        
        # Extract body
        body_lines = []
        docstring = None
        i += 1
        body_start = i
        
        # Find docstring
        if i < len(lines):
            first_body_line = lines[i].strip()
            if first_body_line.startswith('"""') or first_body_line.startswith("'''"):
                docstring_lines = []
                quote = '"""' if first_body_line.startswith('"""') else "'''"
                
                # Single line docstring
                if first_body_line.count(quote) >= 2:
                    docstring = first_body_line.strip(quote).strip()
                    i += 1
                else:
                    # Multi-line docstring
                    docstring_lines.append(first_body_line.strip(quote))
                    i += 1
                    while i < len(lines):
                        line_content = lines[i]
                        if quote in line_content:
                            docstring_lines.append(line_content[:line_content.index(quote)])
                            docstring = '\n'.join(docstring_lines).strip()
                            i += 1
                            break
                        docstring_lines.append(line_content)
                        i += 1
        
        # Extract rest of body
        while i < len(lines):
            curr_line = lines[i]
            
            # Empty line
            if not curr_line.strip():
                body_lines.append(curr_line)
                i += 1
                continue
            
            curr_indent = len(curr_line) - len(curr_line.lstrip())
            
            # Check if we've left the function (same or lower indent + keyword)
            if curr_indent <= indent:
                # Check if it's a new definition
                if def_pattern.match(curr_line) or re.match(r'^\s*class\s+\w+', curr_line):
                    break
                # Check if it's a decorator for next function
                if decorator_pattern.match(curr_line):
                    break
            
            body_lines.append(curr_line)
            i += 1
        
        # Build function info
        func_info = {
            "name": func_name,
            "signature": signature,
            "decorators": decorators if include_decorators else [],
            "docstring": docstring if include_docstring else None,
            "body": '\n'.join(body_lines) if include_body else "",
            "line_start": sig_start - len(decorators),
            "line_end": i - 1,
            "indent": indent,
            "is_async": is_async,
            "params": params,
            "returns": returns
        }
        
        functions.append(func_info)
    
    return functions


# ===============================================================================
# Class Extraction
# ===============================================================================

def _extract_classes(
    text: str,
    include_decorators: bool = True,
    include_docstring: bool = True,
    include_methods: bool = False
) -> List[Dict]:
    """
    Extract all class definitions from Python source.
    
    Args:
        text: Python source code
        include_decorators: Include decorator lines
        include_docstring: Include docstring
        include_methods: Include method signatures (basic)
        
    Returns:
        List of class info dicts:
        {
            "name": str,
            "signature": str,
            "bases": List[str],
            "decorators": List[str],
            "docstring": Optional[str],
            "methods": List[Dict],
            "line_start": int,
            "line_end": int,
            "indent": int
        }
    """
    
    lines = text.splitlines()
    classes = []
    
    # Patterns
    class_pattern = re.compile(r'^(\s*)class\s+(\w+)(\([^)]*\))?:')
    decorator_pattern = re.compile(r'^(\s*)@')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Collect decorators
        decorators = []
        while i < len(lines) and decorator_pattern.match(lines[i]):
            decorators.append(lines[i])
            i += 1
        
        if i >= len(lines):
            break
        
        line = lines[i]
        
        # Match class definition
        class_match = class_pattern.match(line)
        if not class_match:
            i += 1
            continue
        
        indent_str = class_match.group(1)
        indent = len(indent_str)
        class_name = class_match.group(2)
        bases = class_match.group(3) or "()"
        
        signature = line
        class_start = i
        i += 1
        
        # Extract docstring
        docstring = None
        if i < len(lines):
            first_line = lines[i].strip()
            if first_line.startswith('"""') or first_line.startswith("'''"):
                docstring_lines = []
                quote = '"""' if first_line.startswith('"""') else "'''"
                
                # Single line docstring
                if first_line.count(quote) >= 2:
                    docstring = first_line.strip(quote).strip()
                    i += 1
                else:
                    # Multi-line docstring
                    docstring_lines.append(first_line.strip(quote))
                    i += 1
                    while i < len(lines):
                        line_content = lines[i]
                        if quote in line_content:
                            docstring_lines.append(line_content[:line_content.index(quote)])
                            docstring = '\n'.join(docstring_lines).strip()
                            i += 1
                            break
                        docstring_lines.append(line_content)
                        i += 1
        
        # Extract methods (if requested)
        methods = []
        if include_methods:
            method_pattern = re.compile(r'^\s+def\s+(\w+)')
            while i < len(lines):
                curr_line = lines[i]
                
                # Empty line
                if not curr_line.strip():
                    i += 1
                    continue
                
                curr_indent = len(curr_line) - len(curr_line.lstrip())
                
                # Left the class
                if curr_indent <= indent and curr_line.strip():
                    break
                
                # Found a method
                if method_pattern.match(curr_line):
                    # Extract just the method signature
                    method_sig = curr_line.strip()
                    method_name = re.search(r'def\s+(\w+)', method_sig).group(1)
                    methods.append({
                        "name": method_name,
                        "signature": method_sig,
                        "line": i
                    })
                
                i += 1
        else:
            # Skip to end of class
            while i < len(lines):
                curr_line = lines[i]
                if not curr_line.strip():
                    i += 1
                    continue
                
                curr_indent = len(curr_line) - len(curr_line.lstrip())
                if curr_indent <= indent and curr_line.strip():
                    break
                
                i += 1
        
        classes.append({
            "name": class_name,
            "signature": signature,
            "bases": bases.strip('()').split(',') if bases != "()" else [],
            "decorators": decorators if include_decorators else [],
            "docstring": docstring if include_docstring else None,
            "methods": methods,
            "line_start": class_start - len(decorators),
            "line_end": i - 1,
            "indent": indent
        })
    
    return classes


# ===============================================================================
# Import Extraction
# ===============================================================================

def _extract_imports(text: str) -> List[Dict]:
    """
    Extract all import statements from Python source.
    
    Args:
        text: Python source code
        
    Returns:
        List of import info dicts:
        {
            "type": "import" | "from",
            "module": str,           # for "from X import Y", module is X
            "names": List[str],      # imported names
            "statement": str,        # full statement
            "line": int
        }
    """
    
    lines = text.splitlines()
    imports = []
    
    # Patterns
    import_pattern = re.compile(r'^import\s+(.+)')
    from_pattern = re.compile(r'^from\s+(\S+)\s+import\s+(.+)')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue
        
        # From import
        from_match = from_pattern.match(stripped)
        if from_match:
            module = from_match.group(1)
            imports_str = from_match.group(2)
            
            # Parse imported names
            names = []
            for part in imports_str.split(','):
                part = part.strip()
                # Handle "as" aliases
                if ' as ' in part:
                    name = part.split(' as ')[0].strip()
                else:
                    name = part
                names.append(name)
            
            imports.append({
                "type": "from",
                "module": module,
                "names": names,
                "statement": stripped,
                "line": i + 1
            })
            continue
        
        # Regular import
        import_match = import_pattern.match(stripped)
        if import_match:
            imports_str = import_match.group(1)
            
            # Parse imported modules
            names = []
            for part in imports_str.split(','):
                part = part.strip()
                # Handle "as" aliases
                if ' as ' in part:
                    name = part.split(' as ')[0].strip()
                else:
                    name = part
                names.append(name)
            
            imports.append({
                "type": "import",
                "module": None,
                "names": names,
                "statement": stripped,
                "line": i + 1
            })
    
    return imports


# ===============================================================================
# Docstring Extraction
# ===============================================================================

def _extract_docstring(body: str) -> Optional[str]:
    """
    Extract docstring from function/class body.
    
    Args:
        body: Function or class body text
        
    Returns:
        Docstring text or None
    """
    
    lines = body.strip().splitlines()
    if not lines:
        return None
    
    first_line = lines[0].strip()
    
    # Check for docstring
    if not (first_line.startswith('"""') or first_line.startswith("'''")):
        return None
    
    quote = '"""' if first_line.startswith('"""') else "'''"
    
    # Single line docstring
    if first_line.count(quote) >= 2:
        return first_line.strip(quote).strip()
    
    # Multi-line docstring
    docstring_lines = [first_line.strip(quote)]
    
    for line in lines[1:]:
        if quote in line:
            docstring_lines.append(line[:line.index(quote)])
            break
        docstring_lines.append(line)
    
    return '\n'.join(docstring_lines).strip()


# ===============================================================================
# Module Variable Extraction
# ===============================================================================

def _extract_module_variables(text: str) -> List[Dict]:
    """
    Extract module-level variable assignments.
    
    Identifies lines like:
        variable_name = value
        CONSTANT = value
        instance = ClassName(args)
    
    Args:
        text: Python source code
        
    Returns:
        List of variable info dicts:
        {
            "name": str,
            "line": str,
            "line_num": int
        }
    """
    
    lines = text.splitlines()
    variables = []
    
    # Pattern for module-level assignment (no leading whitespace)
    var_pattern = re.compile(r'^([a-zA-Z_]\w*)\s*=')
    
    for i, line in enumerate(lines):
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        # Only match lines with no indentation (module level)
        if line[0].isspace():
            continue
        
        match = var_pattern.match(line)
        if match:
            var_name = match.group(1)
            variables.append({
                "name": var_name,
                "line": line,
                "line_num": i + 1
            })
    
    return variables


# ===============================================================================
# Dependency Analysis
# ===============================================================================

def _extract_function_dependencies(func_info: Dict, all_imports: List[Dict]) -> List[str]:
    """
    Extract import names used in function body.
    
    Args:
        func_info: Function info dict from _extract_functions
        all_imports: All imports from _extract_imports
        
    Returns:
        List of imported names used in function
    """
    
    body = func_info.get("body", "")
    signature = func_info.get("signature", "")
    full_text = signature + "\n" + body
    
    used_imports = []
    
    for imp in all_imports:
        if imp["type"] == "from":
            # Check if any imported names are used
            for name in imp["names"]:
                # Simple word boundary check
                pattern = r'\b' + re.escape(name) + r'\b'
                if re.search(pattern, full_text):
                    used_imports.append(name)
        elif imp["type"] == "import":
            # Check if module name is used
            for name in imp["names"]:
                pattern = r'\b' + re.escape(name) + r'\b'
                if re.search(pattern, full_text):
                    used_imports.append(name)
    
    return used_imports


def _extract_function_with_imports(
    text: str,
    func_name: str,
    include_decorators: bool = True
) -> Optional[Dict]:
    """
    Extract a single function with its required imports.
    
    Args:
        text: Python source code
        func_name: Function name to extract
        include_decorators: Include decorators
        
    Returns:
        Dict with function info and required imports, or None if not found
    """
    
    funcs = _extract_functions(text, include_decorators=include_decorators)
    imports = _extract_imports(text)
    
    # Find the function
    target_func = None
    for func in funcs:
        if func["name"] == func_name:
            target_func = func
            break
    
    if not target_func:
        return None
    
    # Find required imports
    required_imports = _extract_function_dependencies(target_func, imports)
    
    # Filter import statements
    needed_import_stmts = []
    for imp in imports:
        if imp["type"] == "from":
            if any(n in required_imports for n in imp["names"]):
                needed_import_stmts.append(imp["statement"])
        elif imp["type"] == "import":
            if any(n in required_imports for n in imp["names"]):
                needed_import_stmts.append(imp["statement"])
    
    return {
        "function": target_func,
        "imports": needed_import_stmts
    }


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "PYTHON_KEYWORDS",
    "DEFAULT_INDENT",
    "_extract_functions",
    "_extract_classes",
    "_extract_imports",
    "_extract_docstring",
    "_extract_module_variables",
    "_extract_function_dependencies",
    "_extract_function_with_imports",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
