# Path: usekit.tools.keymemory.parser.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
#
#  [Refactored] Thin wrapper over parser_km_sub (single source of truth).
#  All parsing and resolution logic lives in parser_km_sub.
#  KMParser delegates to it — no duplicate logic.
# -----------------------------------------------------------------------------------------------

"""
KeyMemory Parser Module

Thin wrapper over parser_km_sub for backward compatibility.

Parsing engine:
    usekit.classes.data.base.post.sub.parser_km_sub

This module provides the KMParser class interface while
delegating all actual work to parser_km_sub functions.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from usekit.classes.data.base.post.sub.parser_km_sub import (
    parse_anchors,
    resolve_anchors,
    validate_km_format,
    validate_anchor_resolution,
    extract_comments,
    format_km,
    find_anchor_dependencies,
    find_anchor_usage,
    get_anchor_value,
    resolve_anchor,
    KM_ANCHOR_PATTERN,
    KM_UNION_PATTERN,
    KM_REFERENCE_PATTERN,
)


class KMParser:
    """
    Parser for .km (Key Memory) format

    Delegates to parser_km_sub for all parsing and resolution.

    Syntax:
        @ANCHOR = /path/to/location
        @CHILD = @PARENT/subpath
        # comment line
    """

    @staticmethod
    def parse_file(km_path: str | Path) -> Dict[str, str]:
        """
        Parse .km file and return resolved anchor dictionary.

        Delegates to parser_km_sub.parse_anchors() + resolve_anchors().

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

        content = km_path.read_text(encoding="utf-8")
        raw_anchors = parse_anchors(content)
        resolved = resolve_anchors(raw_anchors)

        return resolved

    @staticmethod
    def parse_line(line: str) -> Optional[Tuple[str, str]]:
        """
        Parse single line of .km format.

        Uses KM_ANCHOR_PATTERN from parser_km_sub.

        Args:
            line: Single line from .km file

        Returns:
            (key, value) tuple or None if comment/empty

        Examples:
            "@BASE = /project" -> ('@BASE', '/project')
            "# comment" -> None
            "" -> None
        """
        line = line.strip()

        if not line or line.startswith("#"):
            return None

        if "=" not in line:
            return None

        # Use parser_km_sub pattern (handles inline comments via regex)
        match = KM_ANCHOR_PATTERN.match(line)
        if not match:
            # Check if it looks like an anchor but has invalid syntax
            key_part = line.split("=", 1)[0].strip()
            if key_part.startswith("@"):
                # Union syntax — skip, not an error
                if KM_UNION_PATTERN.match(line):
                    return None
            return None

        anchor_name = "@" + match.group(1)
        anchor_value = match.group(2).strip()

        return (anchor_name, anchor_value)

    @staticmethod
    def resolve_inheritance(raw_anchors: Dict[str, str]) -> Dict[str, str]:
        """
        Resolve @anchor inheritance chains.

        Delegates to parser_km_sub.resolve_anchors() which uses
        token-safe regex substitution (no @A / @AB collisions).

        Args:
            raw_anchors: Dictionary with unresolved references

        Returns:
            Dictionary with fully resolved paths
        """
        return resolve_anchors(raw_anchors)

    # --- Exposed parser_km_sub utilities ---

    @staticmethod
    def validate(content: str) -> List[str]:
        """Validate KM file format. Returns list of errors."""
        return validate_km_format(content)

    @staticmethod
    def validate_resolution(raw_anchors: Dict[str, str]) -> List[str]:
        """Validate that all anchor references can be resolved."""
        return validate_anchor_resolution(raw_anchors)

    @staticmethod
    def dependencies(raw_anchors: Dict[str, str]) -> Dict[str, set]:
        """Build dependency graph of anchors."""
        return find_anchor_dependencies(raw_anchors)

    @staticmethod
    def comments(content: str) -> List[Tuple[int, str]]:
        """Extract full-line comments from KM content."""
        return extract_comments(content)

    @staticmethod
    def format(anchors: Dict[str, str], add_comments: bool = False) -> str:
        """Format anchor dictionary as KM file content."""
        return format_km(anchors, add_comments)
