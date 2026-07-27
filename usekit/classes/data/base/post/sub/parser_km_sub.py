# Path: usekit.classes.data.base.post.sub.parser_km_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for KM parser - anchor parsing, validation, resolution
# Features:
#   - Anchor parsing: Extract @ANCHOR = path definitions
#   - Anchor resolution: Resolve @PARENT inheritance chains
#   - Token-safe reference replacement: avoids @A / @AB collisions
#   - Format validation: Check KM syntax rules
#   - Dependency analysis: detect missing references and circular chains
#   - Utility functions: comments, formatting, usage analysis
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Optional, Set


# ===============================================================================
# Constants
# ===============================================================================

# Anchor:
#   @BASE = /project
#   @SRC = @BASE/src
#   @deep = @test.sub
#   @calc = @PB$calc          ($ = leaf marker, points to file)
#   @card = @JB.srs$cards     (. = path, $ = leaf/file)
#   @card = @JB/srs$cards     (/ = path, same as dot — interchangeable)
KM_ANCHOR_PATTERN = re.compile(
    r"^@([A-Za-z0-9_]+)\s*=\s*(.+?)(?:\s*#.*)?$"
)

# Union preset:
#   @models[] = [@MODEL_CLS | @MODEL_REG | @MODEL_CLU]
#
# Parsing union values is intentionally not part of the Level-1 MVP resolver,
# but the pattern exists so validation can allow this syntax.
KM_UNION_PATTERN = re.compile(
    r"^@([A-Za-z0-9_]+)\[\]\s*=\s*\[(.+?)\](?:\s*#.*)?$"
)

# Reference token:
#   @BASE
#   @SRC
#   @deep
#
# NOTE:
# This pattern is used with regex substitution so @A and @AB do not collide.
KM_REFERENCE_PATTERN = re.compile(r"@([A-Za-z0-9_]+)")

# Leaf marker ($):
#   @PB$calc      → dir_path=None, name="calc"
#   @JB.srs$cards → dir_path="srs", name="cards"
#
# $ separates the pointer (path/directory) from the leaf (file).
# This is the core KM principle: @ = pointer, $ = leaf.
KM_LEAF_MARKER = "$"


# ===============================================================================
# Core Parsing Functions
# ===============================================================================

def parse_anchors(content: str) -> Dict[str, str]:
    """
    Parse KM content and extract anchor definitions.

    This parses normal anchor definitions only:

        @BASE = /project
        @SRC = @BASE/src
        @deep = @test.sub

    Union definitions such as:

        @models[] = [@A | @B]

    are intentionally ignored by this function because unions are a higher-level
    KM feature and should not be mixed with Level-1 path anchor resolution.

    Args:
        content: KM file content as string.

    Returns:
        Dictionary of raw, unresolved anchors.

        {
            "@BASE": "/project",
            "@SRC": "@BASE/src",
            "@MODEL": "@SRC/models",
        }

    Raises:
        ValueError: If duplicate anchor definitions are found.
    """

    anchors: Dict[str, str] = {}

    for line_num, raw_line in enumerate(content.splitlines(), 1):
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if "=" not in line:
            continue

        # Skip union definitions here.
        if KM_UNION_PATTERN.match(line):
            continue

        match = KM_ANCHOR_PATTERN.match(line)
        if not match:
            # Invalid or future syntax. Let validate_km_format() report it if needed.
            continue

        anchor_name = "@" + match.group(1)
        anchor_value = match.group(2).strip()

        if anchor_name in anchors:
            raise ValueError(
                f"Duplicate anchor '{anchor_name}' at line {line_num}"
            )

        anchors[anchor_name] = anchor_value

    return anchors


def resolve_anchors(
    raw_anchors: Dict[str, str],
    max_iterations: int = 100,
) -> Dict[str, str]:
    """
    Resolve anchor inheritance chains safely.

    Handles chains like:

        @BASE = /project
        @SRC = @BASE/src
        @MODELS = @SRC/models

    Also supports route-style tree inheritance strings:

        @test = @jb.test
        @deep = @test.sub

    This function uses token-safe regex substitution instead of raw str.replace(),
    so anchors like @A and @AB do not collide.

    Args:
        raw_anchors: Dictionary with unresolved references.
        max_iterations: Maximum resolution iterations.

    Returns:
        Dictionary with fully resolved anchor values.

    Raises:
        ValueError:
            - If an anchor references an undefined anchor.
            - If a circular dependency exists.
            - If max_iterations is reached.
    """

    errors = validate_anchor_resolution(raw_anchors)
    if errors:
        raise ValueError("; ".join(errors))

    resolved: Dict[str, str] = {}
    remaining: Dict[str, str] = dict(raw_anchors)

    for _ in range(max_iterations):
        if not remaining:
            break

        progress_made = False
        still_remaining: Dict[str, str] = {}

        for anchor, value in remaining.items():
            refs = {"@" + ref for ref in KM_REFERENCE_PATTERN.findall(value)}

            if not refs:
                resolved[anchor] = value
                progress_made = True
                continue

            if refs.issubset(resolved.keys()):
                def replace_ref(match: re.Match[str]) -> str:
                    ref_anchor = "@" + match.group(1)
                    return resolved[ref_anchor]

                resolved[anchor] = KM_REFERENCE_PATTERN.sub(replace_ref, value)
                progress_made = True
            else:
                still_remaining[anchor] = value

        remaining = still_remaining

        if not progress_made and remaining:
            deps = find_anchor_dependencies(remaining)
            raise ValueError(
                f"Circular anchor dependency detected or unresolved chain: {deps}"
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
    Validate KM file format and return a list of errors.

    Checks:
        - Anchor keys start with @.
        - Anchor names are non-empty.
        - Anchor names use only alphanumeric characters and underscore.
        - Duplicate anchor keys are detected.
        - Union keys like @name[] are accepted.

    Notes:
        This function validates key syntax only.
        It does not resolve anchors. Use validate_anchor_resolution() for reference checks.

    Args:
        content: KM file content.

    Returns:
        List of error messages. Empty list means no format errors were found.
    """

    errors: List[str] = []
    seen_keys: Set[str] = set()

    for line_num, raw_line in enumerate(content.splitlines(), 1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key_part = line.split("=", 1)[0].strip()

        # Support union keys:
        #   @models[]
        is_union = key_part.endswith("[]")
        check_key = key_part[:-2] if is_union else key_part

        if not check_key.startswith("@"):
            errors.append(
                f"Line {line_num}: Anchor must start with '@': {key_part}"
            )
            continue

        name_part = check_key[1:]

        if not name_part:
            errors.append(
                f"Line {line_num}: Empty anchor name"
            )
            continue

        if not re.match(r"^[A-Za-z0-9_]+$", name_part):
            errors.append(
                f"Line {line_num}: Invalid anchor name '{key_part}' "
                f"(only alphanumeric and underscore allowed)"
            )
            continue

        duplicate_key = key_part

        if duplicate_key in seen_keys:
            errors.append(
                f"Line {line_num}: Duplicate anchor '{duplicate_key}'"
            )
        else:
            seen_keys.add(duplicate_key)

    return errors


def validate_anchor_resolution(raw_anchors: Dict[str, str]) -> List[str]:
    """
    Validate that all anchor references can be resolved.

    Args:
        raw_anchors: Dictionary of unresolved anchors.

    Returns:
        List of validation errors.

    Example:
        raw = {
            "@BASE": "/project",
            "@SRC": "@BASE/src",
            "@MODEL": "@MISSING/models",
        }

        errors = validate_anchor_resolution(raw)
        # ["Anchor '@MODEL' references undefined '@MISSING'"]
    """

    errors: List[str] = []
    anchor_names = set(raw_anchors.keys())

    for anchor, value in raw_anchors.items():
        refs = KM_REFERENCE_PATTERN.findall(value)

        for ref_name in refs:
            ref_anchor = "@" + ref_name

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
    Extract full-line comments from KM file content.

    Args:
        content: KM file content.

    Returns:
        List of (line_number, comment_text) tuples.
    """

    comments: List[Tuple[int, str]] = []

    for line_num, raw_line in enumerate(content.splitlines(), 1):
        line = raw_line.strip()

        if line.startswith("#"):
            comments.append((line_num, line))

    return comments


def format_km(anchors: Dict[str, str], add_comments: bool = False) -> str:
    """
    Format an anchor dictionary as KM file content.

    Args:
        anchors: Dictionary of anchors.
        add_comments: Add a generated-file header comment.

    Returns:
        Formatted KM file content.
    """

    lines: List[str] = []

    if add_comments:
        lines.append("# Generated KeyMemory file")
        lines.append("")

    for anchor, value in sorted(anchors.items()):
        lines.append(f"{anchor} = {value}")

    return "\n".join(lines)


def find_anchor_dependencies(raw_anchors: Dict[str, str]) -> Dict[str, Set[str]]:
    """
    Build dependency graph of anchors.

    Args:
        raw_anchors: Dictionary of unresolved anchors.

    Returns:
        Dictionary mapping each anchor to the anchors it references.

    Example:
        raw = {
            "@BASE": "/project",
            "@SRC": "@BASE/src",
            "@MODEL": "@SRC/models",
        }

        deps = find_anchor_dependencies(raw)
        # {
        #     "@BASE": set(),
        #     "@SRC": {"@BASE"},
        #     "@MODEL": {"@SRC"},
        # }
    """

    dependencies: Dict[str, Set[str]] = {}

    for anchor, value in raw_anchors.items():
        refs = KM_REFERENCE_PATTERN.findall(value)
        dependencies[anchor] = {"@" + ref for ref in refs}

    return dependencies


def find_anchor_usage(content: str, target_anchor: str) -> List[int]:
    """
    Find all lines where a specific anchor is referenced.

    Definition lines are excluded.

    Args:
        content: KM file content.
        target_anchor: Anchor to search for, with or without '@'.

    Returns:
        List of line numbers where target_anchor is used.
    """

    if not target_anchor.startswith("@"):
        target_anchor = "@" + target_anchor

    usage_lines: List[int] = []

    for line_num, raw_line in enumerate(content.splitlines(), 1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key_part, value_part = line.split("=", 1)
        key_part = key_part.strip()
        value_part = value_part.strip()

        if key_part == target_anchor:
            continue

        refs = {"@" + ref for ref in KM_REFERENCE_PATTERN.findall(value_part)}

        if target_anchor in refs:
            usage_lines.append(line_num)

    return usage_lines


def get_anchor_value(content: str, anchor: str) -> Optional[str]:
    """
    Get raw unresolved anchor value from KM content.

    Args:
        content: KM file content.
        anchor: Anchor name, with or without '@'.

    Returns:
        Raw unresolved value, or None if missing.
    """

    if not anchor.startswith("@"):
        anchor = "@" + anchor

    anchors = parse_anchors(content)
    return anchors.get(anchor)


def resolve_anchor(anchor: str, raw_anchors: Dict[str, str]) -> str:
    """
    Resolve a single anchor from raw anchor dictionary.

    Args:
        anchor: Anchor name, with or without '@'.
        raw_anchors: Raw unresolved anchors.

    Returns:
        Fully resolved anchor value.

    Raises:
        KeyError: If anchor does not exist.
        ValueError: If resolution fails.
    """

    if not anchor.startswith("@"):
        anchor = "@" + anchor

    resolved = resolve_anchors(raw_anchors)

    if anchor not in resolved:
        raise KeyError(f"Anchor not found: {anchor}")

    return resolved[anchor]


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "KM_ANCHOR_PATTERN",
    "KM_UNION_PATTERN",
    "KM_REFERENCE_PATTERN",
    "parse_anchors",
    "resolve_anchors",
    "validate_km_format",
    "validate_anchor_resolution",
    "extract_comments",
    "format_km",
    "find_anchor_dependencies",
    "find_anchor_usage",
    "get_anchor_value",
    "resolve_anchor",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
