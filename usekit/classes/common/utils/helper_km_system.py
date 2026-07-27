# Path: usekit.classes.common.utils.helper_km_system.py
# -----------------------------------------------------------------------------------------------
#  System anchor runtime injection for KM (.km) resolution
#  Created by: THE Little Prince × ROP × FOP
#
#  System anchors are UPPERCASE and auto-generated from sys_const.yaml + runtime BASE_PATH.
#  They are NOT written in .km files.
#
#  Example:
#    @JB = <runtime json/base root>
#    @JS = <runtime json/sub root>
#    @MB = <runtime md/base root>
#    ...
#
#  User .km files inherit from these:
#    @test = @JB.test
#    @deep = @test.sub
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache

from usekit.infra.params_map import FORMAT_CODES, LOCATION_CODES


# ===============================================================================
# System Anchor Generation
# ===============================================================================

def _build_system_anchors() -> Dict[str, str]:
    """
    Build system anchors from FORMAT_CODES × LOCATION_CODES.

    Uses get_smart_path() to resolve each (fmt, loc) pair to an absolute path.

    Returns:
        Dictionary of system anchors.
        Example:
            {
                "@JB": "/storage/.../data/json/base",
                "@JS": "/storage/.../data/json/sub",
                "@MB": "/storage/.../docs/base",
                ...
            }
    """
    from usekit.classes.common.utils.helper_path import get_smart_path

    anchors: Dict[str, str] = {}

    for fmt_code, fmt_name in FORMAT_CODES.items():
        for loc_code, loc_name in LOCATION_CODES.items():
            # Only generate for base/sub (primary route locations)
            # dir/now/tmp/pre/cache are user-specified, not system anchors
            if loc_name not in ("base", "sub"):
                continue

            anchor_name = f"@{fmt_code.upper()}{loc_code.upper()}"

            try:
                path = get_smart_path(fmt=fmt_name, loc=loc_name, ensure_ext=False)
                anchors[anchor_name] = str(path)
            except Exception:
                # Some fmt+loc combinations may not exist (e.g., pkl+sub)
                continue

    return anchors


@lru_cache(maxsize=1)
def get_system_anchors() -> Dict[str, str]:
    """
    Get cached system anchors.

    Cached so that repeated KM resolutions don't regenerate paths.
    Call clear_system_anchor_cache() if BASE_PATH changes at runtime.
    """
    return _build_system_anchors()


def clear_system_anchor_cache() -> None:
    """Clear the system anchor cache (call when BASE_PATH changes)."""
    get_system_anchors.cache_clear()


# ===============================================================================
# KM File Resolution (using parser_km_sub) — with mtime-based caching
# ===============================================================================

# Cache: km_path_str → (mtime, resolved_dict)
_km_resolve_cache: Dict[str, tuple] = {}


def _invalidate_km_cache(km_path: Path) -> bool:
    """Check if cached resolve is still valid. Returns True if cache is stale."""
    key = str(km_path)
    if key not in _km_resolve_cache:
        return True
    cached_mtime, _ = _km_resolve_cache[key]
    try:
        current_mtime = km_path.stat().st_mtime
        return current_mtime != cached_mtime
    except OSError:
        return True


def clear_km_cache() -> None:
    """Clear all km resolve caches. Call when km files are edited."""
    _km_resolve_cache.clear()


def resolve_km_file(
    km_path: Path,
    *,
    debug: bool = False,
) -> Dict[str, str]:
    """
    Load and resolve a .km file with system anchors injected.
    Results are cached by file path + mtime for performance.

    Process:
        1. Check cache (mtime-based invalidation)
        2. Load system anchors (runtime-generated, lru_cached)
        3. Parse user anchors from .km file
        4. Merge: system + user anchors
        5. Resolve inheritance chains via parser_km_sub.resolve_anchors()
        6. Cache result
    """
    # --- Cache check ---
    cache_key = str(km_path)
    if not _invalidate_km_cache(km_path):
        _, cached_resolved = _km_resolve_cache[cache_key]
        if debug:
            print(f"[KM-SYSTEM] Cache hit: {km_path.name}")
        return cached_resolved

    from usekit.classes.data.base.post.sub.parser_km_sub import (
        parse_anchors,
        resolve_anchors,
    )

    # 1. System anchors
    system = get_system_anchors()

    if debug:
        print(f"[KM-SYSTEM] Loaded {len(system)} system anchors")

    # 2. Parse user anchors from file
    content = km_path.read_text(encoding="utf-8")
    user_anchors = parse_anchors(content)

    if debug:
        print(f"[KM-SYSTEM] Parsed {len(user_anchors)} user anchors from {km_path.name}")
        for k, v in user_anchors.items():
            print(f"  {k} = {v}")

    # 3. Merge: system anchors + user anchors
    # User anchors should NOT override system anchors
    merged = dict(system)
    for key, value in user_anchors.items():
        if key in merged:
            if debug:
                print(f"[KM-SYSTEM] WARNING: user anchor {key} shadows system anchor, skipped")
            continue
        merged[key] = value

    # 4. Resolve all inheritance chains
    resolved = resolve_anchors(merged)

    # 5. Convert dots to path separators in resolved values
    # KM syntax uses dots as path separators: @test = @JB.test means @JB/test
    # After resolve_anchors replaces @JB with absolute path,
    # the dot remains as literal: /storage/.../base.test
    # We need to convert these remaining dots to slashes.
    # NOTE: $ (leaf marker) is preserved here — it is split later
    # in resolve_km_alias() for dir_path/name separation.
    for key in list(resolved.keys()):
        val = resolved[key]
        # Replace dots but NOT $ — $ is structural, not a path separator
        # $ is only converted to / in display contexts (uk.info, km_list_aliases)
        resolved[key] = val.replace(".", "/")

    # 6. Process group bindings: [@a | @b | @c] → resolve each member
    # Groups are stored as raw "[...| ...]" strings by parse_anchors.
    # We detect them here and resolve each member to a list.
    group_resolved: Dict[str, Any] = dict(resolved)

    for key, raw_val in user_anchors.items():
        stripped = raw_val.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            inner = stripped[1:-1]
            members = [m.strip() for m in inner.split("|") if m.strip()]

            member_paths = []
            for member in members:
                # member is like "@ai_config" or "@test"
                if member in resolved:
                    member_paths.append(resolved[member])
                elif member in group_resolved:
                    member_paths.append(group_resolved[member])
                else:
                    if debug:
                        print(f"[KM-SYSTEM] Group {key}: member {member} not found, skipped")
                    continue

            group_resolved[key] = member_paths

            if debug:
                print(f"[KM-SYSTEM] Group {key} → {len(member_paths)} members")
                for p in member_paths:
                    print(f"    {p}")

    # 7. Cache result
    try:
        mtime = km_path.stat().st_mtime
        _km_resolve_cache[cache_key] = (mtime, group_resolved)
    except OSError:
        pass

    if debug:
        print(f"[KM-SYSTEM] Resolved {len(group_resolved)} total anchors (cached)")
        # Show only user anchors in debug (system ones are verbose)
        for k in user_anchors:
            if k in group_resolved:
                val = group_resolved[k]
                if isinstance(val, list):
                    print(f"  {k} → [group: {len(val)} paths]")
                else:
                    print(f"  {k} → {val}")

    return group_resolved


def resolve_km_alias(
    alias: str,
    rest_name: str,
    fmt: str,
    loc: str,
    *,
    debug: bool = False,
) -> Optional[Dict[str, str]]:
    """
    Resolve @alias.rest_name using .km route map.

    Process:
        1. Determine route code (fmt_code + loc_code → e.g., "jb")
        2. Find _{route_code}.km in route root
        3. Load & resolve with system anchor injection
        4. Look up @alias → get resolved path
        5. Extract dir_path (relative to route root) + name

    Args:
        alias: Alias name without @ (e.g., "test", "card")
        rest_name: Remaining name after alias (e.g., "test01", "math.001")
        fmt: Format name (e.g., "json")
        loc: Location name (e.g., "base")
        debug: Print resolution details

    Returns:
        {"dir_path": ..., "name": ...} or None if resolution fails.

    Raises:
        FileNotFoundError: If .km file is missing (@ requires km)
        KeyError: If alias is not defined in .km
    """
    from usekit.classes.common.utils.helper_path import get_smart_path

    # 1. Build route code
    fmt_code = None
    for code, name in FORMAT_CODES.items():
        if name == fmt:
            fmt_code = code
            break
    loc_code = None
    for code, name in LOCATION_CODES.items():
        if name == loc:
            loc_code = code
            break

    if not fmt_code or not loc_code:
        raise ValueError(f"Unknown format '{fmt}' or location '{loc}'")

    route_code = fmt_code + loc_code

    # 2. Get route root and find km file
    try:
        route_root = get_smart_path(fmt=fmt, loc=loc, ensure_ext=False)
    except Exception as e:
        raise FileNotFoundError(f"Cannot resolve route root for {fmt}/{loc}: {e}")

    km_path = route_root / f"_{route_code}.km"

    if not km_path.exists():
        raise FileNotFoundError(
            f"KM file not found: {km_path}\n"
            f"@{alias} requires _{route_code}.km in {route_root}"
        )

    # 3. Resolve km file with system anchors
    resolved = resolve_km_file(km_path, debug=debug)

    # 4. Look up @alias
    anchor_key = f"@{alias}"
    if anchor_key not in resolved:
        available = [k for k in resolved if k[1:].islower() or "_" in k[1:]]
        raise KeyError(
            f"Unknown anchor '{anchor_key}' in {km_path.name}\n"
            f"Available user anchors: {available}"
        )

    alias_resolved = resolved[anchor_key]

    # --- Group binding: alias resolves to a list of paths ---
    if isinstance(alias_resolved, list):
        route_root_str = str(route_root)
        dir_paths = []
        for abs_path in alias_resolved:
            # $ leaf marker → / (consistent with single alias)
            abs_path = abs_path.replace("$", "/")
            if abs_path.startswith(route_root_str):
                rel = abs_path[len(route_root_str):].strip("/")
            else:
                rel = abs_path
            dir_paths.append(rel if rel else None)

        if debug:
            print(f"[KM] @{alias} → GROUP ({len(dir_paths)} paths)")
            for dp in dir_paths:
                print(f"[KM]   dir_path = {dp!r}")
            if rest_name:
                print(f"[KM]   name     = {rest_name!r}")

        return {
            "dir_paths": dir_paths,
            "name": rest_name if rest_name else None,
            "is_group": True,
        }

    # --- Single alias (existing logic) ---
    # alias_resolved is absolute (e.g., /storage/.../data/json/base/test)
    # route_root is absolute (e.g., /storage/.../data/json/base)
    # dir_path should be relative (e.g., "test")
    route_root_str = str(route_root)

    # --- $ leaf marker: split pointer from leaf ---
    # @calc = @PB$calc → resolved = "/storage/.../src/base$calc"
    # $ separates the directory path (@) from the file name ($)
    leaf_name = None
    if "$" in alias_resolved:
        pointer_part, leaf_name = alias_resolved.rsplit("$", 1)
        alias_resolved = pointer_part

    if alias_resolved.startswith(route_root_str):
        relative = alias_resolved[len(route_root_str):].strip("/")
    else:
        # Cross-route reference — use as-is
        relative = alias_resolved

    # 6. Build dir_path + name from relative + rest_name + leaf_name
    if rest_name:
        rest_normalized = rest_name.replace(".", "/")
        parts = rest_normalized.rsplit("/", 1)
        if len(parts) == 2:
            # rest has sub-path: e.g., "math.001" → dir="math", name="001"
            base_dir = f"{relative}/{parts[0]}" if relative else parts[0]
            # If $ leaf exists, it becomes part of the dir path
            if leaf_name:
                dir_path = f"{base_dir}/{leaf_name}" if base_dir else leaf_name
            else:
                dir_path = base_dir
            name = parts[1]
        else:
            # rest is just a name: e.g., "test01"
            if leaf_name:
                dir_path = f"{relative}/{leaf_name}" if relative else leaf_name
            else:
                dir_path = relative if relative else None
            name = parts[0]
    elif leaf_name:
        # No rest_name but $ leaf exists: @calc = @PB$calc
        # → leaf_name IS the file name
        dir_path = relative if relative else None
        name = leaf_name
    else:
        dir_path = relative if relative else None
        name = None

    if debug:
        print(f"[KM] @{alias} → {alias_resolved}")
        print(f"[KM]   route_root = {route_root_str}")
        print(f"[KM]   relative   = {relative!r}")
        if leaf_name:
            print(f"[KM]   leaf ($)   = {leaf_name!r}")
        print(f"[KM]   dir_path   = {dir_path!r}")
        print(f"[KM]   name       = {name!r}")

    return {"dir_path": dir_path, "name": name, "is_group": False}


# ===============================================================================
# KM CRUD — High-level km file management via usekit routing
# ===============================================================================

def _get_route_info(fmt: str, loc: str) -> tuple:
    """
    Get route code and route root path for a given fmt/loc pair.

    Returns:
        (route_code, route_root) — e.g. ("jb", Path("/storage/.../data/json/base"))
    """
    from usekit.classes.common.utils.helper_path import get_smart_path

    fmt_code = None
    for code, name in FORMAT_CODES.items():
        if name == fmt:
            fmt_code = code
            break
    loc_code = None
    for code, name in LOCATION_CODES.items():
        if name == loc:
            loc_code = code
            break

    if not fmt_code or not loc_code:
        raise ValueError(f"Unknown format '{fmt}' or location '{loc}'")

    route_code = fmt_code + loc_code
    route_root = get_smart_path(fmt=fmt, loc=loc, ensure_ext=False)

    return route_code, route_root


def km_read(fmt: str, loc: str, *, debug: bool = False) -> Optional[str]:
    """
    Read a km file for the given route.

    Args:
        fmt: Format name (e.g., "json")
        loc: Location name (e.g., "base")

    Returns:
        Raw km file content as string, or None if not found.

    Example:
        content = km_read("json", "base")
        # Returns content of data/json/base/_jb.km
    """
    route_code, route_root = _get_route_info(fmt, loc)
    km_path = route_root / f"_{route_code}.km"

    if not km_path.exists():
        if debug:
            print(f"[KM-CRUD] Not found: {km_path}")
        return None

    content = km_path.read_text(encoding="utf-8")
    if debug:
        print(f"[KM-CRUD] Read {km_path} ({len(content)} chars)")
    return content


def km_write(
    content: str,
    fmt: str,
    loc: str,
    *,
    validate: bool = True,
    debug: bool = False,
) -> Path:
    """
    Write (create or overwrite) a km file for the given route.

    Validates syntax before writing if validate=True.
    Clears km cache after writing.

    Args:
        content: KM file content string
        fmt: Format name (e.g., "json")
        loc: Location name (e.g., "base")
        validate: Validate KM syntax before writing (default True)

    Returns:
        Path to the written km file.

    Example:
        km_write("@test = @JB.test\\n@card = @JB.srs.cards", "json", "base")
    """
    from usekit.classes.data.base.post.sub.parser_km_sub import (
        validate_km_format,
    )

    route_code, route_root = _get_route_info(fmt, loc)
    km_path = route_root / f"_{route_code}.km"

    # Validate syntax
    if validate:
        errors = validate_km_format(content)
        if errors:
            raise ValueError(
                f"KM syntax errors in _{route_code}.km:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

    # Ensure directory exists
    km_path.parent.mkdir(parents=True, exist_ok=True)

    # Write
    km_path.write_text(content, encoding="utf-8")

    # Clear cache so next resolve picks up changes
    clear_km_cache()

    if debug:
        print(f"[KM-CRUD] Wrote {km_path} ({len(content)} chars)")

    return km_path


def km_has(fmt: str, loc: str) -> bool:
    """
    Check if a km file exists for the given route.

    Args:
        fmt: Format name (e.g., "json")
        loc: Location name (e.g., "base")

    Returns:
        True if _{route_code}.km exists.
    """
    route_code, route_root = _get_route_info(fmt, loc)
    return (route_root / f"_{route_code}.km").exists()


def km_delete(fmt: str, loc: str, *, debug: bool = False) -> bool:
    """
    Delete a km file for the given route.

    Clears km cache after deletion.

    Args:
        fmt: Format name (e.g., "json")
        loc: Location name (e.g., "base")

    Returns:
        True if file was deleted, False if it didn't exist.
    """
    route_code, route_root = _get_route_info(fmt, loc)
    km_path = route_root / f"_{route_code}.km"

    if not km_path.exists():
        if debug:
            print(f"[KM-CRUD] Not found (nothing to delete): {km_path}")
        return False

    km_path.unlink()
    clear_km_cache()

    if debug:
        print(f"[KM-CRUD] Deleted {km_path}")

    return True


def km_add_alias(
    alias: str,
    target: str,
    fmt: str,
    loc: str,
    *,
    debug: bool = False,
) -> Path:
    """
    Add a single alias to an existing km file (or create one).

    Does NOT overwrite existing aliases — raises ValueError on duplicate.

    Args:
        alias: Alias name without @ (e.g., "card")
        target: Target value (e.g., "@JB.srs.cards")
        fmt: Format name
        loc: Location name

    Returns:
        Path to the updated km file.

    Example:
        km_add_alias("card", "@JB.srs.cards", "json", "base")
        # Appends: @card = @JB.srs.cards
    """
    from usekit.classes.data.base.post.sub.parser_km_sub import parse_anchors

    content = km_read(fmt, loc) or ""
    anchor_key = f"@{alias}"

    # Check for duplicate
    existing = parse_anchors(content)
    if anchor_key in existing:
        raise ValueError(
            f"Alias '{anchor_key}' already exists in _{_get_route_info(fmt, loc)[0]}.km "
            f"(value: {existing[anchor_key]})"
        )

    # Append
    new_line = f"{anchor_key} = {target}"
    if content and not content.endswith("\n"):
        content += "\n"
    content += new_line + "\n"

    return km_write(content, fmt, loc, debug=debug)


def km_remove_alias(
    alias: str,
    fmt: str,
    loc: str,
    *,
    debug: bool = False,
) -> Path:
    """
    Remove a single alias from a km file.

    Args:
        alias: Alias name without @ (e.g., "card")
        fmt: Format name
        loc: Location name

    Returns:
        Path to the updated km file.

    Raises:
        KeyError: If alias not found.
    """
    from usekit.classes.data.base.post.sub.parser_km_sub import parse_anchors

    content = km_read(fmt, loc)
    if content is None:
        route_code = _get_route_info(fmt, loc)[0]
        raise FileNotFoundError(f"KM file _{route_code}.km not found")

    anchor_key = f"@{alias}"

    # Check existence
    existing = parse_anchors(content)
    if anchor_key not in existing:
        raise KeyError(f"Alias '{anchor_key}' not found in km file")

    # Remove the line (preserve comments and other aliases)
    import re
    pattern = re.compile(
        rf"^@{re.escape(alias)}\s*=\s*.+?(?:\s*#.*)?$",
        re.MULTILINE,
    )
    new_content = pattern.sub("", content)

    # Clean up blank lines (max 1 consecutive)
    new_content = re.sub(r"\n{3,}", "\n\n", new_content).strip() + "\n"

    return km_write(new_content, fmt, loc, debug=debug)


def km_list_aliases(
    fmt: str,
    loc: str,
    *,
    resolve: bool = False,
    debug: bool = False,
) -> Dict[str, str]:
    """
    List all user-defined aliases in a km file.

    Args:
        fmt: Format name
        loc: Location name
        resolve: If True, return fully resolved paths (with system anchors)

    Returns:
        Dictionary of aliases. Keys are anchor names (@alias), values are
        raw definitions (resolve=False) or resolved paths (resolve=True).
    """
    from usekit.classes.data.base.post.sub.parser_km_sub import parse_anchors

    content = km_read(fmt, loc, debug=debug)
    if content is None:
        return {}

    raw = parse_anchors(content)

    if not resolve:
        return raw

    # Resolve with system anchors
    route_code, route_root = _get_route_info(fmt, loc)
    km_path = route_root / f"_{route_code}.km"
    resolved = resolve_km_file(km_path, debug=debug)

    # Return only user anchors (filter out system)
    # Convert $ to / for display ($ is preserved internally for routing)
    result = {}
    for k, v in resolved.items():
        if k in raw:
            if isinstance(v, str):
                result[k] = v.replace("$", "/")
            elif isinstance(v, list):
                result[k] = [p.replace("$", "/") if isinstance(p, str) else p for p in v]
            else:
                result[k] = v
    return result


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    # System anchor management
    "get_system_anchors",
    "clear_system_anchor_cache",
    # KM resolve (internal routing)
    "clear_km_cache",
    "resolve_km_file",
    "resolve_km_alias",
    # KM CRUD (user-facing)
    "km_read",
    "km_write",
    "km_has",
    "km_delete",
    "km_add_alias",
    "km_remove_alias",
    "km_list_aliases",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
