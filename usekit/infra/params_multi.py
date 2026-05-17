# Path: usekit.infra.params_multi.py
# -----------------------------------------------------------------------------------
#  Batch expansion layer for USEKIT name expressions
#
#  Role
#  ----
#  This module provides a thin "batch" layer on top of
#  `normalize_value_params`, so that higher-level APIs can accept
#  compact multi-target expressions such as:
#
#      name = "mmd.m1, m2"
#      name = "md.mm:f1, f2"
#
#  and expand them into a list of normalized parameter dicts.
#
#  Design
#  ------
#  - Core normalizer: `normalize_value_params` (single expression only)
#  - This module:
#      * splits comma-separated expressions
#      * applies context inheritance rules
#      * calls `normalize_value_params` for each logical unit
#
#  Context rules
#  -------------
#  Let tokens be the comma-split pieces after strip():
#
#  1) Absolute token:
#        - token contains any of '@', '/', '.', ':'
#        - always treated as a fully independent expression
#        - directly passed to `normalize_value_params(name=token, **base_kwargs)`
#
#  2) Relative token (no '@', '/', '.', ':'):
#        - uses context from the previous expanded entry (if any)
#
#        Case A: previous entry has `func`
#          e.g. name = "md.mm:f1, f2"
#            - "md.mm:f1"  → module "md/mm", name="mm", func="f1"
#            - "f2"        → same module, func="f2"
#
#        Case B: previous entry has no `func`
#          e.g. name = "mmd.m1, m2"
#            - "mmd.m1"  → dir="mmd", name="m1"
#            - "m2"      → same dir="mmd", name="m2"
#
#  Fallback
#  --------
#  - If no previous context is available (first token, or previous parse failed),
#    a relative token is treated as a simple standalone `name` and passed
#    directly to `normalize_value_params(name=token, **base_kwargs)`.
#
#  Designed by: Little Prince × ROP × USEKIT
# -----------------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from usekit.infra.params_value import normalize_value_params


def _has_special_syntax(token: str) -> bool:
    """
    Return True if token looks like a 'full' expression with its own syntax:

        - contains '@' (alias / inline spec)
        - contains '/' or '.' (path-like)
        - contains ':' (func suffix)
    """
    return any(ch in token for ch in ("@", "/", ".", ":"))


def _expand_single_absolute(name: str, base_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expand a single absolute token via normalize_value_params.

    Parameters
    ----------
    name : str
        Raw name expression (one token).
    base_kwargs : dict
        Baseline kwargs to pass along (fmt, loc, dir_path, etc.).

    Returns
    -------
    dict
        Normalized parameter dictionary.
    """
    return normalize_value_params(name=name, **base_kwargs)


def _inherit_for_relative(
    token: str,
    prev: Dict[str, Any],
    base_kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build kwargs for a relative token using the context from `prev`.

    Rules
    -----
    - If prev has 'func':
        treat token as a new function on the same module:
            - inherit alias, fmt, loc, dir_path, name
            - set func = token
    - Else:
        treat token as a new name in the same directory:
            - inherit alias, fmt, loc, dir_path
            - set name = token

    Notes
    -----
    - We intentionally do NOT inherit arbitrary keys.
      Only routing-related fields (alias, fmt, loc, dir_path, name)
      are carried over.
    """
    kwargs: Dict[str, Any] = dict(base_kwargs)  # shallow copy

    # Inherit selected routing fields from prev
    for key in ("alias", "fmt", "loc", "dir_path"):
        if key in prev and prev[key] is not None:
            kwargs[key] = prev[key]

    if "func" in prev and prev.get("func"):
        # Case A: previous entry had a function specified
        # → same module, different func
        if "name" in prev and prev.get("name"):
            kwargs.setdefault("name", prev["name"])
        if "dir_path" in prev and prev.get("dir_path"):
            kwargs.setdefault("dir_path", prev["dir_path"])
        kwargs["func"] = token
    else:
        # Case B: previous had no func
        # → same directory, different name
        if "dir_path" in prev and prev.get("dir_path"):
            kwargs.setdefault("dir_path", prev["dir_path"])
        kwargs["name"] = token

    return normalize_value_params(**kwargs)


def expand_name_batch(
    *,
    name: Optional[str] = None,
    names: Optional[Iterable[str]] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Expand comma-separated or list-based name expressions into a batch.

    Parameters
    ----------
    name : str, optional
        A single string expression which may contain commas, e.g.:
            "mmd.m1, m2"
            "md.mm:f1, f2"
            "@js.data/session.task:run, clean"
    names : iterable of str, optional
        Explicit list of expressions. If provided together with `name`,
        the two sources are concatenated in that order.
    **kwargs :
        Additional keyword arguments (fmt, loc, dir_path, alias, etc.)
        passed down to `normalize_value_params`.

    Returns
    -------
    list of dict
        Each item is a normalized parameter dict as returned by
        `normalize_value_params`.
    """
    tokens: List[str] = []

    # Collect tokens from single 'name' (comma-separated)
    if isinstance(name, str) and name.strip():
        parts = [p.strip() for p in name.split(",") if p.strip()]
        tokens.extend(parts)

    # Collect tokens from 'names' iterable
    if names is not None:
        for n in names:
            if isinstance(n, str) and n.strip():
                tokens.append(n.strip())

    # No input at all → empty batch
    if not tokens:
        return []

    batch: List[Dict[str, Any]] = []
    prev: Optional[Dict[str, Any]] = None
    base_kwargs: Dict[str, Any] = dict(kwargs)  # baseline copy

    for idx, token in enumerate(tokens):
        # Absolute token: own syntax
        if idx == 0 or _has_special_syntax(token) or prev is None:
            params = _expand_single_absolute(token, base_kwargs)
        else:
            # Relative token: use previous context if possible
            params = _inherit_for_relative(token, prev, base_kwargs)

        batch.append(params)
        prev = params

    return batch


__all__ = [
    "expand_name_batch",
]