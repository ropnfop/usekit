# Path: usekit.tools.keymemory.parser.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# -----------------------------------------------------------------------------------------------

"""
KeyMemory Parser Module

Parses .km (Key Memory) format files
Supports:
- @ anchors
- = binding  
- # comments
- @anchor inheritance chains
"""

from pathlib import Path
from typing import Dict, Tuple, Optional


class KMParser:
    """
    Parser for .km (Key Memory) format
    
    Syntax:
        @ANCHOR = /path/to/location
        @CHILD = @PARENT/subpath
        # comment line
    """
    
    @staticmethod
    def parse_file(km_path: str | Path) -> Dict[str, str]:
        """
        Parse .km file and return resolved anchor dictionary
        
        Args:
            km_path: Path to .km file
            
        Returns:
            Dictionary of resolved anchors {
                '@BASE': '/content/drive/MyDrive/PROJECT',
                '@SRC': '/content/drive/MyDrive/PROJECT/src',
                ...
            }
        """
        km_path = Path(km_path)
        
        if not km_path.exists():
            raise FileNotFoundError(f".km file not found: {km_path}")
        
        # Parse all lines
        raw_anchors = {}
        with open(km_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                result = KMParser.parse_line(line)
                if result:
                    key, value = result
                    if key in raw_anchors:
                        raise ValueError(
                            f"Duplicate anchor '{key}' at line {line_num}"
                        )
                    raw_anchors[key] = value
        
        # Resolve inheritance
        resolved = KMParser.resolve_inheritance(raw_anchors)
        
        return resolved
    
    @staticmethod
    def parse_line(line: str) -> Optional[Tuple[str, str]]:
        """
        Parse single line of .km format
        
        Args:
            line: Single line from .km file
            
        Returns:
            (key, value) tuple or None if comment/empty
            
        Examples:
            "@BASE = /project" -> ('@BASE', '/project')
            "# comment" -> None
            "" -> None
        """
        # Strip whitespace
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return None
        
        # Skip comment lines
        if line.startswith('#'):
            return None
        
        # Must contain =
        if '=' not in line:
            return None
        
        # Split on first =
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Key must start with @
        if not key.startswith('@'):
            raise ValueError(f"Anchor must start with @: {key}")
        
        # Remove inline comments from value
        if '#' in value:
            value = value.split('#')[0].strip()
        
        return (key, value)
    
    @staticmethod
    def resolve_inheritance(raw_anchors: Dict[str, str]) -> Dict[str, str]:
        """
        Resolve @anchor inheritance chains
        
        Handles chains like:
            @BASE = /project
            @SRC = @BASE/src
            @MODELS = @SRC/models
            
        Args:
            raw_anchors: Dictionary with unresolved references
            
        Returns:
            Dictionary with fully resolved paths
        """
        resolved = {}
        max_iterations = 100  # Prevent infinite loops
        
        # Keep resolving until all anchors are resolved
        remaining = dict(raw_anchors)
        
        for iteration in range(max_iterations):
            if not remaining:
                break
            
            progress_made = False
            still_remaining = {}
            
            for anchor, value in remaining.items():
                # Check if value contains any @ references
                if '@' in value:
                    # Try to resolve all @ references in value
                    resolved_value = value
                    all_resolved = True
                    
                    # Find all @ANCHOR references in value
                    parts = resolved_value.split('@')
                    new_parts = [parts[0]]  # First part has no @
                    
                    for part in parts[1:]:
                        # Extract anchor name (up to / or end)
                        if '/' in part:
                            ref_name, rest = part.split('/', 1)
                            ref_anchor = '@' + ref_name
                            
                            if ref_anchor in resolved:
                                # Replace with resolved value
                                new_parts.append(resolved[ref_anchor] + '/' + rest)
                            else:
                                # Not yet resolved
                                all_resolved = False
                                new_parts.append(part)
                        else:
                            # Entire rest is anchor name
                            ref_anchor = '@' + part
                            
                            if ref_anchor in resolved:
                                new_parts.append(resolved[ref_anchor])
                            else:
                                all_resolved = False
                                new_parts.append(part)
                    
                    if all_resolved:
                        # Join parts (skip first @ that we split on)
                        resolved_value = ''.join(new_parts)
                        resolved[anchor] = resolved_value
                        progress_made = True
                    else:
                        # Keep for next iteration
                        still_remaining[anchor] = value
                else:
                    # No @ references, directly resolved
                    resolved[anchor] = value
                    progress_made = True
            
            remaining = still_remaining
            
            if not progress_made and remaining:
                # Circular dependency or missing reference
                raise ValueError(
                    f"Cannot resolve anchors (circular dependency or missing reference): "
                    f"{list(remaining.keys())}"
                )
        
        if remaining:
            raise ValueError(f"Max iterations reached, unresolved: {list(remaining.keys())}")
        
        return resolved
