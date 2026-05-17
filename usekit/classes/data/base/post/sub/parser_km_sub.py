# Path: usekit.classes.data.base.post.sub.parser_km_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for KM parser - anchor parsing, validation, resolution
# Features:
#   - Anchor parsing: Extract @ANCHOR = /path definitions
#   - Anchor resolution: Resolve @PARENT inheritance chains
#   - Format validation: Check KM syntax rules
#   - Utility functions: Comments, formatting, analysis
# -----------------------------------------------------------------------------------------------

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set


# ===============================================================================
# Constants
# ===============================================================================

KM_ANCHOR_PATTERN = re.compile(r'^@(\w+)\s*=\s*(.+?)(?:\s*#.*)?$')
KM_REFERENCE_PATTERN = re.compile(r'@(\w+)')


# ===============================================================================
# Core Parsing Functions
# ===============================================================================

def parse_anchors(content: str) -> Dict[str, str]:
    """
    Parse KM content and extract anchor definitions.
    
    Args:
        content: KM file content as string
        
    Returns:
        Dictionary of raw anchors (unresolved)
        {
            '@BASE': '/project',
            '@SRC': '@BASE/src',
            '@MODEL': '@SRC/models'
        }
        
    Example:
        content = '''
        @BASE = /project
        @SRC = @BASE/src
        # comment line
        @MODEL = @SRC/models
        '''
        
        anchors = parse_anchors(content)
        # {'@BASE': '/project', '@SRC': '@BASE/src', '@MODEL': '@SRC/models'}
    """
    
    anchors = {}
    
    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip comment lines
        if line.startswith('#'):
            continue
        
        # Must contain =
        if '=' not in line:
            continue
        
        # Parse anchor definition
        match = KM_ANCHOR_PATTERN.match(line)
        if not match:
            # Invalid format but not an error (might be multi-line or special case)
            continue
        
        anchor_name = '@' + match.group(1)
        anchor_value = match.group(2).strip()
        
        # Check for duplicates
        if anchor_name in anchors:
            raise ValueError(
                f"Duplicate anchor '{anchor_name}' at line {line_num}"
            )
        
        anchors[anchor_name] = anchor_value
    
    return anchors


def resolve_anchors(raw_anchors: Dict[str, str], max_iterations: int = 100) -> Dict[str, str]:
    """
    Resolve anchor inheritance chains.
    
    Handles chains like:
        @BASE = /project
        @SRC = @BASE/src
        @MODELS = @SRC/models
    
    Args:
        raw_anchors: Dictionary with unresolved references
        max_iterations: Maximum resolution iterations (prevents infinite loops)
        
    Returns:
        Dictionary with fully resolved paths
        
    Raises:
        ValueError: If circular dependency or missing reference detected
        
    Example:
        raw = {
            '@BASE': '/project',
            '@SRC': '@BASE/src',
            '@MODEL': '@SRC/models'
        }
        
        resolved = resolve_anchors(raw)
        # {
        #     '@BASE': '/project',
        #     '@SRC': '/project/src',
        #     '@MODEL': '/project/src/models'
        # }
    """
    
    resolved = {}
    remaining = dict(raw_anchors)
    
    for iteration in range(max_iterations):
        if not remaining:
            break
        
        progress_made = False
        still_remaining = {}
        
        for anchor, value in remaining.items():
            # Check if value contains any @ references
            if '@' not in value:
                # No references, directly resolved
                resolved[anchor] = value
                progress_made = True
                continue
            
            # Try to resolve all @ references in value
            resolved_value = value
            all_resolved = True
            
            # Find all @ANCHOR references in value
            refs = KM_REFERENCE_PATTERN.findall(value)
            
            for ref_name in refs:
                ref_anchor = '@' + ref_name
                
                if ref_anchor in resolved:
                    # Replace with resolved value
                    resolved_value = resolved_value.replace(ref_anchor, resolved[ref_anchor])
                else:
                    # Not yet resolved
                    all_resolved = False
                    break
            
            if all_resolved:
                resolved[anchor] = resolved_value
                progress_made = True
            else:
                # Keep for next iteration
                still_remaining[anchor] = value
        
        remaining = still_remaining
        
        if not progress_made and remaining:
            # Circular dependency or missing reference
            raise ValueError(
                f"Cannot resolve anchors (circular dependency or missing reference): "
                f"{list(remaining.keys())}"
            )
    
    if remaining:
        raise ValueError(
            f"Max iterations ({max_iterations}) reached, unresolved: {list(remaining.keys())}"
        )
    
    return resolved


# ===============================================================================
# Validation Functions
# ===============================================================================

def validate_km_format(content: str) -> List[str]:
    """
    Validate KM file format and return list of errors.
    
    Checks:
    - Anchor names start with @
    - Lines with @ must have =
    - No duplicate anchors
    - Valid anchor name format (alphanumeric + underscore)
    
    Args:
        content: KM file content
        
    Returns:
        List of error messages (empty if valid)
        
    Example:
        content = '''
        @BASE = /project
        INVALID = /path
        @BASE = /duplicate
        '''
        
        errors = validate_km_format(content)
        # [
        #     "Line 2: Anchor must start with '@': INVALID",
        #     "Line 3: Duplicate anchor '@BASE'"
        # ]
    """
    
    errors = []
    seen_anchors = set()
    
    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Must contain =
        if '=' not in line:
            continue
        
        # Extract key part
        key_part = line.split('=', 1)[0].strip()
        
        # Check @ prefix
        if not key_part.startswith('@'):
            errors.append(
                f"Line {line_num}: Anchor must start with '@': {key_part}"
            )
            continue
        
        # Validate anchor name format
        anchor_name = key_part
        name_part = anchor_name[1:]  # Remove @
        
        if not name_part:
            errors.append(
                f"Line {line_num}: Empty anchor name"
            )
            continue
        
        if not re.match(r'^[A-Za-z0-9_]+$', name_part):
            errors.append(
                f"Line {line_num}: Invalid anchor name '{anchor_name}' "
                f"(only alphanumeric and underscore allowed)"
            )
            continue
        
        # Check for duplicates
        if anchor_name in seen_anchors:
            errors.append(
                f"Line {line_num}: Duplicate anchor '{anchor_name}'"
            )
        else:
            seen_anchors.add(anchor_name)
    
    return errors


def validate_anchor_resolution(raw_anchors: Dict[str, str]) -> List[str]:
    """
    Validate that all anchor references can be resolved.
    
    Args:
        raw_anchors: Dictionary of unresolved anchors
        
    Returns:
        List of validation errors
        
    Example:
        raw = {
            '@BASE': '/project',
            '@SRC': '@BASE/src',
            '@MODEL': '@MISSING/models'  # @MISSING not defined
        }
        
        errors = validate_anchor_resolution(raw)
        # ["Anchor '@MODEL' references undefined '@MISSING'"]
    """
    
    errors = []
    anchor_names = set(raw_anchors.keys())
    
    for anchor, value in raw_anchors.items():
        # Find all references in value
        refs = KM_REFERENCE_PATTERN.findall(value)
        
        for ref_name in refs:
            ref_anchor = '@' + ref_name
            
            if ref_anchor not in anchor_names:
                errors.append(
                    f"Anchor '{anchor}' references undefined '{ref_anchor}'"
                )
    
    return errors


# ===============================================================================
# Utility Functions
# ===============================================================================

def extract_comments(content: str) -> List[Tuple[int, str]]:
    """
    Extract all comments from KM file.
    
    Args:
        content: KM file content
        
    Returns:
        List of (line_number, comment_text) tuples
        
    Example:
        content = '''
        # Main config
        @BASE = /project
        # Source paths
        @SRC = @BASE/src
        '''
        
        comments = extract_comments(content)
        # [(1, '# Main config'), (3, '# Source paths')]
    """
    
    comments = []
    
    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        
        if line.startswith('#'):
            comments.append((line_num, line))
    
    return comments


def format_km(anchors: Dict[str, str], add_comments: bool = False) -> str:
    """
    Format anchor dictionary as KM file content.
    
    Args:
        anchors: Dictionary of anchors
        add_comments: Add section comments
        
    Returns:
        Formatted KM file content
        
    Example:
        anchors = {
            '@BASE': '/project',
            '@SRC': '/project/src',
            '@MODEL': '/project/src/models'
        }
        
        content = format_km(anchors, add_comments=True)
        # '''
        # # Generated KeyMemory file
        # @BASE = /project
        # @SRC = /project/src
        # @MODEL = /project/src/models
        # '''
    """
    
    lines = []
    
    if add_comments:
        lines.append("# Generated KeyMemory file")
        lines.append("")
    
    # Sort anchors for consistent output
    sorted_anchors = sorted(anchors.items())
    
    for anchor, value in sorted_anchors:
        lines.append(f"{anchor} = {value}")
    
    return "\n".join(lines)


def find_anchor_dependencies(raw_anchors: Dict[str, str]) -> Dict[str, Set[str]]:
    """
    Build dependency graph of anchors.
    
    Args:
        raw_anchors: Dictionary of unresolved anchors
        
    Returns:
        Dictionary mapping each anchor to its dependencies
        
    Example:
        raw = {
            '@BASE': '/project',
            '@SRC': '@BASE/src',
            '@MODEL': '@SRC/models'
        }
        
        deps = find_anchor_dependencies(raw)
        # {
        #     '@BASE': set(),
        #     '@SRC': {'@BASE'},
        #     '@MODEL': {'@SRC'}
        # }
    """
    
    dependencies = {}
    
    for anchor, value in raw_anchors.items():
        refs = KM_REFERENCE_PATTERN.findall(value)
        dependencies[anchor] = {'@' + ref for ref in refs}
    
    return dependencies


def find_anchor_usage(content: str, target_anchor: str) -> List[int]:
    """
    Find all lines where a specific anchor is referenced.
    
    Args:
        content: KM file content
        target_anchor: Anchor to search for (e.g., '@BASE')
        
    Returns:
        List of line numbers where anchor is used
        
    Example:
        content = '''
        @BASE = /project
        @SRC = @BASE/src
        @MODEL = @BASE/models
        @DATA = /data
        '''
        
        usage = find_anchor_usage(content, '@BASE')
        # [2, 3]  (lines with @BASE references, not definition)
    """
    
    usage_lines = []
    
    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        
        # Skip comments
        if line.startswith('#'):
            continue
        
        # Skip empty lines
        if not line:
            continue
        
        # Parse anchor definition
        if '=' in line:
            key_part, value_part = line.split('=', 1)
            key_part = key_part.strip()
            value_part = value_part.strip()
            
            # Skip if this is the definition line
            if key_part == target_anchor:
                continue
            
            # Check if target anchor is referenced in value
            if target_anchor in value_part:
                usage_lines.append(line_num)
    
    return usage_lines


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "parse_anchors",
    "resolve_anchors",
    "validate_km_format",
    "validate_anchor_resolution",
    "extract_comments",
    "format_km",
    "find_anchor_dependencies",
    "find_anchor_usage",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
