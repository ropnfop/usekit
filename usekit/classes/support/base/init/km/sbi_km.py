# Path: usekit.classes.support.base.init.km.sbi_km.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# — memory is emotion —
#
# KM Support Handler — uk
#
# Usage:
#   from usekit import uk
#
#   uk.read("json", "base")
#   uk.write(content, "json", "base")
#   uk.add("card", "@JB.srs.cards", "json", "base")
#   uk.list("json", "base", resolve=True)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


class _KitNamespace:
    """
    Simple namespace for cherry-picked functions.

    Allows attribute access: kit.add(3, 5)
    """

    def __init__(self, name: str):
        self._name = name
        self._functions = {}

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            self._functions[key] = value

    def __getattr__(self, key):
        if key.startswith("_"):
            raise AttributeError(key)
        try:
            return self._functions[key]
        except KeyError:
            available = ", ".join(self._functions.keys())
            raise AttributeError(
                f"Kit '@{self._name}' has no function '{key}'. "
                f"Available: {available}"
            )

    def __repr__(self):
        funcs = ", ".join(self._functions.keys())
        return f"<Kit @{self._name}: {funcs}>"

    def __dir__(self):
        return list(self._functions.keys())


class KMHandler:
    """
    KeyMemory (.km) management support.

    Provides a clean interface for km file CRUD and alias management.
    Delegates to helper_km_system functions.

    Usage:
        uk.read("json", "base")                          # read _jb.km content
        uk.write(content, "json", "base")                # write _jb.km
        uk.has("json", "base")                           # check existence
        uk.delete("json", "base")                        # delete _jb.km

        uk.add("card", "@JB.srs.cards", "json", "base")  # add alias
        uk.remove("card", "json", "base")                 # remove alias
        uk.list("json", "base")                           # list aliases (raw)
        uk.list("json", "base", resolve=True)             # list aliases (resolved)

        uk.clear()                                        # clear km cache
    """

    # ========================================================================
    # CRUD — km file level
    # ========================================================================

    def read(self, fmt: str, loc: str, *, debug: bool = False) -> Optional[str]:
        """
        Read km file raw content.

        Args:
            fmt: Format name (e.g., "json", "yaml", "md")
            loc: Location name (e.g., "base", "sub")

        Returns:
            Raw km file content as string, or None if not found.

        Example:
            uk.read("json", "base")   # reads _jb.km
            uk.read("md", "base")     # reads _mb.km
        """
        from usekit.classes.common.utils.helper_km_system import km_read
        return km_read(fmt, loc, debug=debug)

    def write(
        self,
        content: str,
        fmt: str,
        loc: str,
        *,
        validate: bool = True,
        debug: bool = False,
    ) -> Path:
        """
        Write (create or overwrite) a km file.

        Validates syntax before writing. Clears cache automatically.

        Args:
            content: KM file content string
            fmt: Format name
            loc: Location name
            validate: Validate KM syntax before writing (default True)

        Returns:
            Path to the written km file.

        Example:
            uk.write("@test = @JB.test", "json", "base")
        """
        from usekit.classes.common.utils.helper_km_system import km_write
        return km_write(content, fmt, loc, validate=validate, debug=debug)

    def has(self, fmt: str, loc: str) -> bool:
        """
        Check if a km file exists for the given route.

        Example:
            uk.has("json", "base")   # True if _jb.km exists
        """
        from usekit.classes.common.utils.helper_km_system import km_has
        return km_has(fmt, loc)

    def delete(self, fmt: str, loc: str, *, debug: bool = False) -> bool:
        """
        Delete a km file. Clears cache automatically.

        Returns:
            True if deleted, False if it didn't exist.

        Example:
            uk.delete("json", "sub")  # deletes _js.km
        """
        from usekit.classes.common.utils.helper_km_system import km_delete
        return km_delete(fmt, loc, debug=debug)

    # ========================================================================
    # Alias Management — single alias level
    # ========================================================================

    def add(
        self,
        alias: str,
        target: str,
        fmt: str,
        loc: str,
        *,
        debug: bool = False,
    ) -> Path:
        """
        Add a single alias to a km file (or create one).

        Raises ValueError if alias already exists.

        Args:
            alias: Alias name without @ (e.g., "card")
            target: Target value (e.g., "@JB.srs.cards")
            fmt: Format name
            loc: Location name

        Returns:
            Path to the updated km file.

        Example:
            uk.add("card", "@JB.srs.cards", "json", "base")
            # appends: @card = @JB.srs.cards
        """
        from usekit.classes.common.utils.helper_km_system import km_add_alias
        return km_add_alias(alias, target, fmt, loc, debug=debug)

    def remove(
        self,
        alias: str,
        fmt: str,
        loc: str,
        *,
        debug: bool = False,
    ) -> Path:
        """
        Remove a single alias from a km file.

        Raises KeyError if alias not found.

        Example:
            uk.remove("card", "json", "base")
        """
        from usekit.classes.common.utils.helper_km_system import km_remove_alias
        return km_remove_alias(alias, fmt, loc, debug=debug)

    def list(
        self,
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
            resolve: If True, return fully resolved absolute paths

        Returns:
            Dictionary of aliases.

        Example:
            uk.list("json", "base")
            # {'@test': '@JB.test', '@card': '@JB.srs.cards'}

            uk.list("json", "base", resolve=True)
            # {'@test': '/storage/.../data/json/base/test', ...}
        """
        from usekit.classes.common.utils.helper_km_system import km_list_aliases
        return km_list_aliases(fmt, loc, resolve=resolve, debug=debug)

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear(self) -> None:
        """
        Clear all km resolve caches.

        Call after editing km files externally (outside uk.write/add/remove).
        uk.write(), uk.add(), uk.remove() clear cache automatically.

        Example:
            uk.clear()
        """
        from usekit.classes.common.utils.helper_km_system import (
            clear_km_cache,
            clear_system_anchor_cache,
        )
        clear_km_cache()
        clear_system_anchor_cache()

    # ========================================================================
    # Info / Debug
    # ========================================================================

    def anchors(self) -> Dict[str, str]:
        """
        Show all system anchors (runtime-generated).

        Returns:
            Dictionary of system anchors.

        Example:
            uk.anchors()
            # {'@JB': '/storage/.../data/json/base', '@JS': '...', ...}
        """
        from usekit.classes.common.utils.helper_km_system import get_system_anchors
        return get_system_anchors()

    def info(self, fmt: str, loc: str) -> None:
        """
        Print km file summary for quick inspection.

        Example:
            uk.info("json", "base")
        """
        exists = self.has(fmt, loc)
        if not exists:
            from usekit.classes.common.utils.helper_km_system import _get_route_info
            route_code, route_root = _get_route_info(fmt, loc)
            print(f"[KM] _{route_code}.km — not found in {route_root}")
            return

        aliases = self.list(fmt, loc)
        resolved = self.list(fmt, loc, resolve=True)

        from usekit.classes.common.utils.helper_km_system import _get_route_info
        route_code, _ = _get_route_info(fmt, loc)

        print(f"[KM] _{route_code}.km — {len(aliases)} aliases")
        for key in aliases:
            raw = aliases[key]
            res = resolved.get(key, "?")
            if isinstance(res, list):
                print(f"  {key} = {raw}")
                print(f"    → [group: {len(res)} paths]")
            else:
                print(f"  {key} = {raw}")
                print(f"    → {res}")

    def __repr__(self) -> str:
        return "<KMHandler>"

    # ========================================================================
    # Level 2 — Transform Pipeline
    # ========================================================================

    def flatten(
        self,
        data: dict,
        *,
        depth: str = "shallow",
    ) -> list:
        """
        Flatten nested dict to KM leaf table.

        Each row: {"path": str, "key": str, "value": Any}

        Args:
            data: Nested dict
            depth: "shallow" (default) or "deep"

        Returns:
            List of leaf records.

        Example:
            leaf = uk.flatten({"ai": {"config": {"model": "qwen"}}})
            # [{"path": "ai/config", "key": "model", "value": "qwen"}]
        """
        from usekit.classes.common.utils.helper_km_transform import km_flatten
        return km_flatten(data, depth=depth)

    def reconstruct(self, leaf_table: list) -> dict:
        """
        Reconstruct nested dict from KM leaf table.

        Args:
            leaf_table: List of leaf records [{path, key, value}, ...]

        Returns:
            Nested dict restored from leaf table.

        Example:
            data = uk.reconstruct([
                {"path": "ai/config", "key": "model", "value": "qwen"}
            ])
            # {"ai": {"config": {"model": "qwen"}}}
        """
        from usekit.classes.common.utils.helper_km_transform import km_reconstruct
        return km_reconstruct(leaf_table)

    def query(self, leaf_table: list, query_str: str) -> list:
        """
        Execute KQL query on leaf table.

        Supported queries:
            SELECT * WHERE path LIKE 'ai/%'
            UPDATE SET value = 'gpt-4' WHERE key = 'model'
            DELETE WHERE path LIKE 'srs/%'
            INSERT path='ai/config' key='max_tokens' value=1000

        Args:
            leaf_table: Input leaf table
            query_str: KQL query string

        Returns:
            Modified/filtered leaf table.
        """
        from usekit.classes.common.utils.helper_km_transform import km_query
        return km_query(leaf_table, query_str)

    def pipe(self, data: dict, queries: list, *, depth: str = "shallow") -> dict:
        """
        Flatten → chain KQL queries → reconstruct.

        Args:
            data: Input nested dict
            queries: List of KQL query strings
            depth: Flatten depth ("shallow" or "deep")

        Returns:
            Reconstructed dict after all queries applied.

        Example:
            result = uk.pipe(data, [
                "SELECT * WHERE path LIKE 'ai/%'",
                "UPDATE SET value = 'gpt-4' WHERE key = 'model'",
            ])
        """
        from usekit.classes.common.utils.helper_km_transform import km_pipe
        return km_pipe(data, queries, depth=depth)

    # ========================================================================
    # Support — Function Cherry-Pick Loader
    # ========================================================================

    def support(
        self,
        kit_name: str,
        fmt: str = "pyp",
        loc: str = "base",
        *,
        debug: bool = False,
    ):
        """
        Load a function kit defined in a km file.

        A kit is a tuple-style alias that lists modules and their functions:

            @my_kit = ("@calc: add, multiply", "@demo: report")

        support() imports each module via @alias, extracts the specified
        functions, and returns them as a namespace object.

        Args:
            kit_name: Kit alias name without @ (e.g., "my_kit")
            fmt: Format name (default "pyp")
            loc: Location name (default "base")

        Returns:
            Namespace object with all cherry-picked functions as attributes.

        Example:
            km = '''
            @calc = @PB$calc
            @demo = @PB$demo
            @my_kit = ("@calc: add, multiply", "@demo: report")
            '''
            uk.write(km, "pyp", "base")

            kit = uk.support("my_kit")
            kit.add(3, 5)           # 8
            kit.multiply(4, 7)      # 28
            kit.report("Alice", 95) # {'name': 'Alice', ...}
        """
        from usekit.classes.common.utils.helper_km_system import (
            km_list_aliases,
            resolve_km_file,
            _get_route_info,
        )

        # 1. Get raw aliases
        # Allow both "my_kit" and "@my_kit"
        kit_name = kit_name.lstrip("@")
        aliases = km_list_aliases(fmt, loc)
        anchor_key = f"@{kit_name}"

        if anchor_key not in aliases:
            raise KeyError(
                f"Kit '{anchor_key}' not found in km file. "
                f"Available: {list(aliases.keys())}"
            )

        raw_value = aliases[anchor_key]

        # 2. Parse tuple-style kit definition
        # ("@calc: add, multiply", "@demo: report")
        kit_members = self._parse_kit(raw_value, kit_name)

        if debug:
            print(f"[KM-SUPPORT] @{kit_name} → {len(kit_members)} members")

        # 3. Import each module and extract functions
        from usekit import u

        namespace = _KitNamespace(kit_name)

        for module_alias, func_names in kit_members:
            # Use u.ipb("@alias") to import via km routing
            import_pattern = f"@{module_alias}"

            # Get the right import method based on fmt
            import_method = getattr(u, f"i{self._fmt_code(fmt)}{self._loc_code(loc)}", None)
            if import_method is None:
                raise ValueError(f"No import method for fmt={fmt}, loc={loc}")

            mod = import_method(import_pattern)

            if debug:
                print(f"[KM-SUPPORT]   @{module_alias} → {func_names}")

            for fn_name in func_names:
                fn_name = fn_name.strip()
                if not hasattr(mod, fn_name):
                    raise AttributeError(
                        f"Module '@{module_alias}' has no function '{fn_name}'"
                    )
                # Duplicate check
                if fn_name in namespace._functions:
                    raise ValueError(
                        f"Duplicate function '{fn_name}' in kit '@{kit_name}'. "
                        f"Already loaded from another module."
                    )
                setattr(namespace, fn_name, getattr(mod, fn_name))

        return namespace

    def _parse_kit(self, raw_value: str, kit_name: str) -> list:
        """
        Parse kit definition string into [(module_alias, [func_names]), ...]

        Input:  '("@calc: add, multiply", "@demo: report")'
        Output: [("calc", ["add", "multiply"]), ("demo", ["report"])]
        """
        # Strip outer parens and quotes
        value = raw_value.strip()
        if value.startswith("(") and value.endswith(")"):
            value = value[1:-1]

        # Split by ", " (quoted string boundaries)
        # Handle: "@calc: add, multiply", "@demo: report"
        members = []
        current = ""
        in_quotes = False
        for ch in value:
            if ch == '"':
                in_quotes = not in_quotes
            elif ch == ',' and not in_quotes:
                if current.strip():
                    members.append(current.strip().strip('"'))
                current = ""
                continue
            current += ch
        if current.strip():
            members.append(current.strip().strip('"'))

        # Parse each member: "@calc: add, multiply" → ("calc", ["add", "multiply"])
        result = []
        for member in members:
            member = member.strip().strip('"')
            if ": " not in member and ":" not in member:
                raise ValueError(
                    f"Invalid kit member in @{kit_name}: '{member}'. "
                    f"Expected format: '@alias: func1, func2'"
                )

            alias_part, funcs_part = member.split(":", 1)
            alias = alias_part.strip().lstrip("@")
            func_names = [f.strip() for f in funcs_part.split(",")]
            result.append((alias, func_names))

        return result

    def _fmt_code(self, fmt: str) -> str:
        """Get single-char format code: json→j, pyp→p, etc."""
        from usekit.infra.params_map import FORMAT_CODES
        for code, name in FORMAT_CODES.items():
            if name == fmt:
                return code
        return fmt[0]

    def _loc_code(self, loc: str) -> str:
        """Get single-char location code: base→b, sub→s, etc."""
        from usekit.infra.params_map import LOCATION_CODES
        for code, name in LOCATION_CODES.items():
            if name == loc:
                return code
        return loc[0]


# ========================================================================
# Singleton instance
# ========================================================================

uk = KMHandler()

__all__ = ["KMHandler", "uk"]
