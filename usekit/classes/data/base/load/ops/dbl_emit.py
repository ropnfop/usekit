# -----------------------------------------------------------------------------------------------
#  Emit Operation - Memory-only serialization (no file I/O)
#  Created by: THE Little Prince × ROP × FOP
#  Pure data transformation: dict → string, string → dict, etc.
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from typing import Union

from usekit.infra.io_signature import params_for_emit, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.data.base.load.sub.dbl_emit_sub import proc_emit_data
from usekit.classes.data.base.load.sub.dbl_common_sub import _filter_dump_kwargs


# ===============================================================================
# Parameter Filtering
# ===============================================================================

# Parameters used only at ops layer (should NOT be passed to proc/parser)
OPS_ONLY_PARAMS = {
    # Ops layer processing
    "keydata", "default", "recursive", "find_all", "create_missing",
    "walk", "case_sensitive",

    # Future features
    "k", "kv", "kc", "kf",

    # System layer (ops control)
    "fmt", "mode", "mode_sub", "debug", "type",

    # User layer (path building - NOT used in emit)
    "name", "path", "loc", "cus",

    # Internal params
    "dir_path", "mod",
}

# Emit must be memory-only. Remove write/file-only kwargs so they never reach dumps().
EMIT_DISALLOWED_KWARGS = {
    # write / file-layer concepts
    "append", "append_mode", "overwrite", "safe",
    "encoding", "newline", "errors",
    # any other file-only knobs you may have upstream
    "file", "fp", "stream",
}


def _extract_parser_kwargs(params: dict, fmt: str) -> dict:
    """
    Extract parameters safe for parser.dumps()/parser.loads().

    NOTE:
    _filter_dump_kwargs was originally designed for dump(file). Even with for_file=False,
    some write-only options can survive filtering. Emit must never forward those.
    """
    # Remove ops-only params first
    candidate_params = {k: v for k, v in params.items() if k not in OPS_ONLY_PARAMS}

    # Apply existing format whitelist (best-effort)
    filtered_params = _filter_dump_kwargs(fmt, for_file=False, **candidate_params)

    # Hard block: write/file-only kwargs must never pass into dumps()
    for k in EMIT_DISALLOWED_KWARGS:
        filtered_params.pop(k, None)

    return filtered_params


# ===============================================================================
# Main Emit Operation
# ===============================================================================

@log_and_raise
def emit_operation(**kwargs) -> Union[str, dict, list, bytes]:
    """
    Memory-only serialization operation (no file I/O).
    """

    # Extract parameters
    p = params_for_emit(**kwargs)

    # Warn about future features (k, kv, kc, kf)
    warn_future_features(p)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Force memory-only restriction
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # If user provided name -> reject (emit is memory-only)
    if p.get("name") is not None:
        raise ValueError(
            "emit operation does not support 'name' parameter (memory-only).\n"
            "For file operations, use write operation instead.\n"
            "For memory serialization, remove 'name' parameter."
        )

    # Force loc to 'mem' (do not rely on signature default)
    # If user explicitly requested non-mem -> raise with guidance.
    if p.get("loc") not in (None, "mem"):
        fmt_letter = (p.get("fmt") or "j")[0]
        raise ValueError(
            f"emit operation only supports 'mem' location, got: '{p['loc']}'.\n"
            "Emit is for memory-only serialization without file I/O.\n\n"
            f"For file operations with location '{p['loc']}', use write instead:\n"
            f"  u.w{fmt_letter}{p['loc'][0]}(data, 'filename')\n\n"
            "For memory serialization:\n"
            f"  u.e{fmt_letter}m(data)"
        )

    # Enforce
    p["loc"] = "mem"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Validate data
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p.get("data") is None:
        raise ValueError(
            "emit operation requires 'data' parameter.\n"
            "Provide the data to serialize."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3] Debug
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p.get("debug"):
        print(f"[{p['fmt'].upper()}] Emit (memory-only, type={p['type']})")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [4] Extract parser kwargs (dumps/loads safe)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    parser_kwargs = _extract_parser_kwargs(p, p["fmt"])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [5] Perform memory serialization
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    return proc_emit_data(
        p["fmt"],
        p["data"],
        type=p["type"],
        **parser_kwargs,
    )


__all__ = ["emit_operation"]