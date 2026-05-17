# Path: usekit.tools.convert.common.convert_auto.py
# ------------------------------------------------------------
#  Generate "trio" auto: class / simple / wrap
#
#  Example:
#     convert_trio("txt", "csv")                # auto mode detection
#     convert_trio("txt", "csv", mode="data")   # force data mode
# ------------------------------------------------------------

from __future__ import annotations

from typing import List
from usekit.tools.convert.common.convert import convert_by_name_v2


def convert_trio(old_fmt: str, new_fmt: str, mode: str = "auto", loc: str = "dir") -> List[str]:
    """
    Convert 3 standard files:
        dbi_class_<fmt>.py
        dbi_simple_<fmt>.py
        dbi_wrap_<fmt>.py

    Args:
      old_fmt/new_fmt: format tokens (e.g., "txt" -> "csv")
      mode: "auto" | "navi" | "data"
      loc: "dir" | "name" | "path"
    """
    names = [
        f"dbi_class_{old_fmt}",
        f"dbi_simple_{old_fmt}",
        f"dbi_wrap_{old_fmt}",
    ]

    outputs: List[str] = []
    for name in names:
        print(f"\n[TRIO] converting -> {name}")
        out = convert_by_name_v2(name, old_fmt, new_fmt, loc=loc, mode=mode)
        outputs.append(out)

    print("\n[TRIO] All 3 conversions completed.")
    return outputs