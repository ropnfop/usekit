# Path: usekit.classes.common.utils.helper_km_method.py
# -----------------------------------------------------------------------------------------------
#  KM Method-level binding parser (concept verification)
#  Created by: THE Little Prince × ROP × FOP
#
#  Syntax:
#    @my_kit = ("@file_alias: func1, func2", "@other_alias: func3, func4")
#
#  This enables cherry-pick import:
#    e.support("@my_kit")
#    → imports only func1, func2 from file_alias
#    → imports only func3, func4 from other_alias
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


# ===============================================================================
# Method Binding Types
# ===============================================================================

class MethodBinding:
    """Single file → methods binding."""
    
    __slots__ = ("alias", "methods")
    
    def __init__(self, alias: str, methods: List[str]):
        self.alias = alias        # e.g., "@my_01"
        self.methods = methods    # e.g., ["add", "divide"]
    
    def __repr__(self):
        return f"MethodBinding({self.alias} → [{', '.join(self.methods)}])"


class MethodGroup:
    """Group of method bindings = user's custom toolkit."""
    
    __slots__ = ("name", "bindings")
    
    def __init__(self, name: str, bindings: List[MethodBinding]):
        self.name = name              # e.g., "@my_kit"
        self.bindings = bindings      # list of MethodBinding
    
    def __repr__(self):
        lines = [f"MethodGroup({self.name}):"]
        for b in self.bindings:
            lines.append(f"  {b}")
        return "\n".join(lines)
    
    @property
    def all_methods(self) -> List[Tuple[str, str]]:
        """Return [(alias, method), ...] flat list."""
        result = []
        for b in self.bindings:
            for m in b.methods:
                result.append((b.alias, m))
        return result


# ===============================================================================
# Parser
# ===============================================================================

# Pattern: "@alias: func1, func2"
_BINDING_PATTERN = re.compile(
    r'["\']?\s*(@\w+)\s*:\s*([^"\']+?)\s*["\']?$'
)


def parse_method_binding(value: str) -> Optional[MethodGroup]:
    """
    Parse method binding syntax from km value.
    
    Input format:
        ("@my_01: add, divide", "@my_02: ai, send")
    
    Returns:
        MethodGroup with parsed bindings, or None if not method syntax.
    
    Example:
        >>> val = '("@math: add, divide", "@ai: send, query")'
        >>> group = parse_method_binding(val)
        >>> group.bindings[0].alias
        '@math'
        >>> group.bindings[0].methods
        ['add', 'divide']
    """
    stripped = value.strip()
    
    # Must start with ( and end with )
    if not (stripped.startswith("(") and stripped.endswith(")")):
        return None
    
    inner = stripped[1:-1].strip()
    
    # Split by comma-separated quoted strings
    # "...", "..." or '...', '...'
    parts = re.findall(r'["\']([^"\']+)["\']', inner)
    
    if not parts:
        return None
    
    bindings = []
    
    for part in parts:
        part = part.strip()
        
        # Parse: @alias: func1, func2
        if ":" not in part:
            continue
        
        alias_part, methods_part = part.split(":", 1)
        alias = alias_part.strip()
        
        if not alias.startswith("@"):
            continue
        
        methods = [m.strip() for m in methods_part.split(",") if m.strip()]
        
        if methods:
            bindings.append(MethodBinding(alias=alias, methods=methods))
    
    return MethodGroup(name="", bindings=bindings) if bindings else None


def is_method_binding(value: str) -> bool:
    """Check if a km value is method binding syntax."""
    stripped = value.strip()
    return (
        stripped.startswith("(")
        and stripped.endswith(")")
        and ":" in stripped
        and "@" in stripped
    )


# ===============================================================================
# Integration with KM resolve
# ===============================================================================

def resolve_method_group(
    group: MethodGroup,
    resolved_anchors: Dict[str, str],
    *,
    debug: bool = False,
) -> List[Dict]:
    """
    Resolve a MethodGroup's aliases to actual file paths.
    
    Args:
        group: Parsed MethodGroup
        resolved_anchors: Fully resolved anchor dict from resolve_km_file()
    
    Returns:
        List of {"path": resolved_path, "methods": [func_names]}
    
    Example:
        >>> resolve_method_group(group, {"@my_01": "/storage/.../math_helper"})
        [{"path": "/storage/.../math_helper", "methods": ["add", "divide"]}]
    """
    results = []
    
    for binding in group.bindings:
        if binding.alias in resolved_anchors:
            resolved_path = resolved_anchors[binding.alias]
            
            entry = {
                "alias": binding.alias,
                "path": resolved_path,
                "methods": binding.methods,
            }
            results.append(entry)
            
            if debug:
                print(f"[KM-METHOD] {binding.alias} → {resolved_path}")
                print(f"  methods: {binding.methods}")
        else:
            if debug:
                print(f"[KM-METHOD] WARNING: {binding.alias} not found in resolved anchors")
    
    return results


# ===============================================================================
# Demo / Test
# ===============================================================================

def _demo():
    """Quick concept verification."""
    
    print("=== KM Method Binding - Concept Verification ===\n")
    
    # 1. Parse
    km_value = '("@my_01: add, divide", "@my_02: ai, send")'
    print(f"Input: {km_value}")
    
    group = parse_method_binding(km_value)
    group.name = "@my_kit"
    print(f"\n{group}")
    
    # 2. Flat method list
    print(f"\nAll methods:")
    for alias, method in group.all_methods:
        print(f"  {alias}.{method}()")
    
    # 3. Resolve with mock anchors
    mock_resolved = {
        "@my_01": "/storage/emulated/0/projects/pj01/src/base/utils/math_helper",
        "@my_02": "/storage/emulated/0/projects/pj01/src/base/tools/ai_client",
    }
    
    print(f"\nResolved:")
    results = resolve_method_group(group, mock_resolved, debug=True)
    
    # 4. What e.support would do
    print(f"\n=== e.support('@my_kit') would execute: ===")
    for r in results:
        methods_str = ", ".join(r["methods"])
        print(f"  from {r['path']} import {methods_str}")


if __name__ == "__main__":
    _demo()


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "MethodBinding",
    "MethodGroup",
    "parse_method_binding",
    "is_method_binding",
    "resolve_method_group",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
