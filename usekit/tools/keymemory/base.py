# Path: usekit.tools.keymemory.base.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
#
#  [Refactored] KeyMemory now supports two modes:
#    1. Standalone: KMParser.parse_file() — raw .km files (no system anchors)
#    2. USEKIT-integrated: helper_km_system.resolve_km_file() — with system anchors
# -----------------------------------------------------------------------------------------------

"""
KeyMemory Base Module

Core KeyMemory class for .km format handling.

Standalone mode:
    km = KeyMemory.load("paths.km")

USEKIT-integrated mode (with system anchor injection):
    km = KeyMemory.load_route("json", "base")
"""

from pathlib import Path
from typing import Dict, Optional, Any, List
from usekit.tools.keymemory.parser import KMParser


class KeyMemory:
    """
    KeyMemory class for managing .km format anchors

    Usage:
        # Standalone (raw .km, no system anchors)
        km = KeyMemory.load("paths.km")
        path = km.resolve("@MODEL_CLS")

        # USEKIT-integrated (system anchors injected)
        km = KeyMemory.load_route("json", "base")
        path = km.resolve("@card")

        # Dict-like access
        base = km["@BASE"]
        src = km.get("@SRC", default="/default/src")
    """

    def __init__(self, anchors: Optional[Dict[str, str]] = None):
        """
        Initialize KeyMemory

        Args:
            anchors: Dictionary of resolved anchors
        """
        self._anchors = anchors or {}

    @classmethod
    def load(cls, km_path: str | Path) -> 'KeyMemory':
        """
        Load KeyMemory from .km file (standalone, no system anchors).

        Uses KMParser which delegates to parser_km_sub.

        Args:
            km_path: Path to .km file

        Returns:
            KeyMemory instance with loaded anchors

        Example:
            km = KeyMemory.load("config/paths.km")
        """
        anchors = KMParser.parse_file(km_path)
        return cls(anchors)

    @classmethod
    def load_route(
        cls,
        fmt: str,
        loc: str,
        *,
        debug: bool = False,
    ) -> 'KeyMemory':
        """
        Load KeyMemory for a USEKIT route with system anchor injection.

        Uses helper_km_system.resolve_km_file() which:
        - Generates system anchors (@JB, @JS, @MB, ...) from runtime
        - Merges system + user anchors
        - Resolves inheritance chains
        - Caches by mtime

        Args:
            fmt: Format name (e.g., "json", "yaml", "md")
            loc: Location name (e.g., "base", "sub")
            debug: Print resolution details

        Returns:
            KeyMemory instance with system + user anchors resolved

        Example:
            km = KeyMemory.load_route("json", "base")
            path = km.resolve("@card")
        """
        from usekit.classes.common.utils.helper_km_system import resolve_km_file
        from usekit.classes.common.utils.helper_path import get_smart_path
        from usekit.infra.params_map import FORMAT_CODES, LOCATION_CODES

        # Build route code → km filename
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
        km_path = route_root / f"_{route_code}.km"

        if not km_path.exists():
            raise FileNotFoundError(
                f"KM file not found: {km_path}\n"
                f"Expected _{route_code}.km in {route_root}"
            )

        resolved = resolve_km_file(km_path, debug=debug)
        return cls(resolved)

    def resolve(self, anchor_name: str) -> Path:
        """
        Resolve anchor to Path object

        Args:
            anchor_name: Anchor name (e.g., '@BASE', '@card')

        Returns:
            Path object for the resolved anchor

        Raises:
            KeyError: If anchor not found
        """
        if anchor_name not in self._anchors:
            available = ', '.join(self._anchors.keys())
            raise KeyError(
                f"Anchor '{anchor_name}' not found. "
                f"Available: {available}"
            )

        value = self._anchors[anchor_name]

        # Group binding returns list — wrap as list of Paths
        if isinstance(value, list):
            return [Path(p) for p in value]

        return Path(value)

    def user_anchors(self) -> Dict[str, str]:
        """
        Get only user-defined anchors (lowercase / snake_case keys).

        Filters out system anchors (@JB, @JS, etc.)

        Returns:
            Dictionary of user anchors only
        """
        return {
            k: v for k, v in self._anchors.items()
            if k[1:].islower() or "_" in k[1:]
        }

    def system_anchors(self) -> Dict[str, str]:
        """
        Get only system anchors (UPPERCASE keys).

        Returns:
            Dictionary of system anchors only
        """
        return {
            k: v for k, v in self._anchors.items()
            if k[1:].isupper()
        }

    # --- Dict-like interface (unchanged) ---

    def get(self, key: str, default: Any = None) -> Optional[str]:
        """Dict-like get with default"""
        return self._anchors.get(key, default)

    def __getitem__(self, key: str) -> str:
        """Dict-like access: km['@BASE']"""
        if key not in self._anchors:
            available = ', '.join(self._anchors.keys())
            raise KeyError(
                f"Anchor '{key}' not found. "
                f"Available: {available}"
            )
        return self._anchors[key]

    def __contains__(self, key: str) -> bool:
        """Check if anchor exists: '@BASE' in km"""
        return key in self._anchors

    def __len__(self) -> int:
        """Number of anchors: len(km)"""
        return len(self._anchors)

    def __repr__(self) -> str:
        """String representation"""
        return f"<KeyMemory with {len(self._anchors)} anchors>"

    def keys(self):
        """Get all anchor names"""
        return self._anchors.keys()

    def values(self):
        """Get all anchor values"""
        return self._anchors.values()

    def items(self):
        """Get all anchor items"""
        return self._anchors.items()

    def to_dict(self) -> Dict[str, str]:
        """Export as dictionary"""
        return dict(self._anchors)
