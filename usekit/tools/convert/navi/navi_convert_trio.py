# Path: usekit.tools.convert.navi.navi_convert_trio.py
# ------------------------------------------------------------
#  Generate "3종 세트" auto: class / simple / wrap
#  Example:
#     convert_trio("txt", "csv")
#     convert_trio("csv", "json")
# ------------------------------------------------------------

from usekit.tools.convert.navi.navi_convert import convert_by_name_v2

def convert_trio(old_fmt: str, new_fmt: str):
    """
    Convert 3 standard files:
        nbi_class_<fmt>.py
        nbi_simple_<fmt>.py
        nbi_wrap_<fmt>.py
    """
    names = [
        f"nbi_class_{old_fmt}",
        f"nbi_simple_{old_fmt}",
        f"nbi_wrap_{old_fmt}",
    ]

    outputs = []
    for name in names:
        print(f"\n[TRIO] converting → {name}")
        out = convert_by_name_v2(name, old_fmt, new_fmt)
        outputs.append(out)

    print("\n[TRIO] All 3 conversions completed.")
    return outputs