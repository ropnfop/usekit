# Path: usekit.tools.convert.navi.navi_convert.py
# -----------------------------------------------------------------------------------------------
#  ROP × THE Little Prince × FOP
#  Universal Format Auto-Converter for usekit (Final Version)
#  Features:
#   1) convert_format: txt → csv, txt → yaml, csv → json, etc.
#   2) convert_by_name: find_operation(fmt="pyp") 기반 자동 경로 찾기 → 변환
#   3) convert_all_simple: 프로젝트 전체 포맷 일괄 변환
# -----------------------------------------------------------------------------------------------

import os, re, shutil

# ========== CORE ENGINE ======================================================

def convert_format(src: str, old: str, new: str, dst: str = None):
    """
    Main convert engine:
        convert_format("nbi_simple_txt.py", "txt", "csv")
    """
    if dst is None:
        dst = src.replace(old, new)

    # Backup original
    backup = src + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(src, backup)

    print(f"[INFO] Converting {src} ({old} → {new})")
    print(f"[INFO] Output → {dst}")

    with open(src, "r", encoding="utf-8") as f:
        text = f.read()

    # ----------------------------------------
    # 1) Lowercase txt → csv
    # ----------------------------------------
    text = text.replace(old, new)

    # ----------------------------------------
    # 2) Uppercase Txt → Csv
    # ----------------------------------------
    old_cap = old.capitalize()
    new_cap = new.capitalize()
    text = text.replace(old_cap, new_cap)

    # ----------------------------------------
    # 3) obj: t → obj: c
    # ----------------------------------------
    text = re.sub(rf"obj:\s*{old[0]}", f"obj: {new[0]}", text)

    # ----------------------------------------
    # 4) #    obj: t → #    obj: c
    # ----------------------------------------
    text = re.sub(rf"#\s*obj:\s*{old[0]}", f"#    obj: {new[0]}", text)

    # ----------------------------------------
    # 5) 3-letter alias
    #    ptb → pcb, gtb → gcb, stb → scb 등
    # ----------------------------------------
    old_obj = old[0]
    new_obj = new[0]
    alias_pattern = rf"([pflgs]){old_obj}([bnsdtpc])"
    alias_repl    = rf"\1{new_obj}\2"
    text = re.sub(alias_pattern, alias_repl, text)

    # ----------------------------------------
    # 6) wrap-layer 함수명
    #    get_txt_base → get_csv_base
    # ----------------------------------------
    wrap_pattern = rf"_(path|find|list|get|set)_{old}_"
    wrap_repl    = rf"_\1_{new}_"
    text = re.sub(wrap_pattern, wrap_repl, text)

    # ----------------------------------------
    # 7) import nbi_wrap_txt → nbi_wrap_csv
    # ----------------------------------------
    text = text.replace(f"nbi_wrap_{old}", f"nbi_wrap_{new}")

    # ----------------------------------------
    # 8) Header alias section:
    #    (pt*) → (pc*), (ft*) → (fc*), ...
    # ----------------------------------------
    # Example pattern: "# PATH (pt*)" or "# FIND (ft*)"
    header_pattern = rf"\(([pflgs]){old_obj}\*\)"
    header_repl    = rf"(\1{new_obj}*)"
    text = re.sub(header_pattern, header_repl, text)
    
    # ----------------------------------------
    # Save file
    # ----------------------------------------
    # Ensure destination directory exists
    dst_dir = os.path.dirname(dst)
    if dst_dir and not os.path.exists(dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
        print(f"[MKDIR] Created directory → {dst_dir}")
    
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)

    print("[DONE] Format conversion completed.")
    return dst


# ========== AUTO-FIND + CONVERT ==============================================

def convert_by_name(name: str, old: str, new: str, loc="dir"):
    """
    find_operation(fmt="pyp")로 자동 경로 찾고 변환하는 함수
    
    Example:
        convert_by_name("nbi_simple_txt", "txt", "csv")
    
    Features:
        - Automatically finds source file using find_operation
        - Replaces format in path (txt → csv, json → yaml, etc.)
        - Creates destination directory if not exists
        - Preserves file structure
    """
    from usekit.classes.navi.base.load.ops.nbl_find import find_operation
    from pathlib import Path

    results = find_operation(
        fmt="pyp",
        name=name,
        walk=True,
        loc=loc
    )

    if not results:
        raise FileNotFoundError(f"[ERROR] No .py file found for '{name}'")

    src = Path(results[0])
    
    # Smart replacement: txt → csv in path
    # Example: .../wrap/txt/nbi_simple_txt.py → .../wrap/csv/nbi_simple_csv.py
    src_str = str(src)
    
    # Replace in both directory path and filename
    dst_str = src_str.replace(f"/{old}/", f"/{new}/")  # Directory
    dst_str = dst_str.replace(f"_{old}", f"_{new}")    # Filename
    
    dst = Path(dst_str)
    
    print(f"[AUTO] Found source → {src}")
    print(f"[AUTO] Target path  → {dst}")
    
    return convert_format(str(src), old, new, str(dst))


def convert_by_name_v2(name: str, old: str, new: str, loc="dir"):
    """
    usekit Path 유틸 사용 버전 (가장 깔끔)
    
    Example:
        convert_by_name_v2("nbi_simple_txt", "txt", "json")
    
    Features:
        - Uses find_operation to get exact file
        - Uses path_operation(mk=True) to auto-create destination directory
        - Pure usekit style - no manual os.makedirs
    """
    from usekit.classes.navi.base.load.ops.nbl_find import find_operation
    from usekit.classes.navi.base.load.ops.nbl_path import path_operation
    from pathlib import Path

    # Find source file
    src_results = find_operation(
        fmt="pyp",
        name=name,
        walk=True,
        loc=loc
    )

    if not src_results:
        raise FileNotFoundError(f"[ERROR] No .py file found for '{name}'")

    src = Path(src_results[0])
    
    # Build destination path
    src_str = str(src)
    dst_str = src_str.replace(f"/{old}/", f"/{new}/")
    dst_str = dst_str.replace(f"_{old}", f"_{new}")
    dst = Path(dst_str)
    
    # Auto-create destination directory using path_operation
    # Just create the parent directory of destination file
    dst.parent.mkdir(parents=True, exist_ok=True)
    print(f"[MKDIR] Directory ready → {dst.parent}")
    
    print(f"[AUTO] Source → {src}")
    print(f"[AUTO] Target → {dst}")
    
    return convert_format(str(src), old, new, str(dst))


# ========== PROJECT-WIDE BULK CONVERT ========================================

def convert_all_simple(old="txt", new="csv"):
    """
    프로젝트 전체 *_txt.py → *_csv.py 일괄 변환
    Example:
        convert_all_simple("txt", "csv")
    """
    from usekit.classes.navi.base.load.ops.nbl_find import find_operation

    pattern = f"*_{old}"
    results = find_operation(fmt="pyp", name=pattern, walk=True, loc="dir", mk=True)

    if not results:
        print("[WARN] No files found matching", pattern)
        return []

    outputs = []
    for r in results:
        src = str(r)
        dst = src.replace(old, new)
        print(f"[BULK] {src} → {dst}")
        outputs.append(convert_format(src, old, new, dst))

    return outputs


# ========== __all__ ===========================================================

__all__ = [
    "convert_format",
    "convert_by_name",
    "convert_by_name_v2",
    "convert_all_simple",
]