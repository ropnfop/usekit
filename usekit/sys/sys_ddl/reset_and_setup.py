#!/usr/bin/env python3
# Clean-reset helper: backup old DBs (1 zip), delete them, then setup builds a fresh
# usekit.db from 01~04 seeds. v1 decision: NO migration — old data is discarded.
#
# SAFETY: key rotation is a SEPARATE manual step (do it FIRST, regardless of this).
# Run example:
#   python reset_and_setup.py /path/to/project
import sys, os, time, zipfile, shutil
from pathlib import Path

def reset(project_path: str):
    proj = Path(project_path)
    sysdb = proj / ".usekit" / "sys" / "sys_db"
    targets = ["llm.db","llm.db-wal","llm.db-shm","task.db","usekit.db",
               "usekit.db-wal","usekit.db-shm"]
    existing = [sysdb / t for t in targets if (sysdb / t).exists()]

    # 1) backup ONE zip (archive) — DB files as-is (user decision)
    if existing:
        archive_dir = proj / ".usekit" / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        zpath = archive_dir / f"db_backup_{stamp}.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in existing:
                z.write(f, arcname=f.name)
        print(f"[backup] {len(existing)} files -> {zpath}")
    else:
        print("[backup] no existing DB files found (already clean?)")

    # 2) delete old DBs
    for f in existing:
        try: f.unlink(); print(f"[delete] {f.name}")
        except Exception as e: print(f"[delete] FAIL {f.name}: {e}")

    # 3) hand off to setup (builds fresh usekit.db from seeds)
    print("[next] run usekit setup → seeds 01_TSK,02_TSK_IDX,03_META,04_META_SEED build usekit.db")
    print("[next] then switch lli_db write-path to usekit.db (code step)")
    print("[REMINDER] rotate the exposed Groq key NOW if not done — deletion does NOT undo exposure.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: reset_and_setup.py <project_path>"); sys.exit(1)
    reset(sys.argv[1])
