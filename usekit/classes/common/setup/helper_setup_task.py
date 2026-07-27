# Path: usekit.classes.common.setup.helper_setup_task
# -----------------------------------------------------------------------------------------------
# Task-manager opt-in installer for use.setup()
# -----------------------------------------------------------------------------------------------
# Runs only when the user enables "task manager" during `uk setup`.
#
# Layer: this is usekit's OWN work DB, not project data.
#   .usekit/sys/sys_ddl/*.sql    <- seed DDL (copied from package bundle)
#   .usekit/sys/sys_db/usekit.db <- unified support DB (TSK_* + meta tables)
#
# Folders mirror SYS_PATH (sys_const.yaml: SYS_PATH.ddl / SYS_PATH.db),
# anchored at <project>/.usekit/sys . No hardcoded absolute paths.
#
# pip-installed usekit lives read-only in site-packages, so seeds are copied
# out to the project's .usekit first, then loaded -- same pattern as the
# .env / sys_const.yaml config copy.
# -----------------------------------------------------------------------------------------------

from pathlib import Path


_USEKIT_DIR = ".usekit"          # PROJECT_CONFIG_DIR
_SYS = "sys"
_BUNDLE_DDL = "sys/sys_ddl"      # seed source inside the installed package


def setup_task_manager(project_path: Path, verbose: bool = True) -> bool:
    """
    Opt-in: copy TSK seed DDL into .usekit/sys/sys_ddl, then build
    .usekit/sys/sys_db/usekit.db. Idempotent (IF NOT EXISTS + skip-existing).

    Returns True if usekit.db has the expected tables afterward.
    """
    import shutil
    import sqlite3

    sys_dir = project_path / _USEKIT_DIR / _SYS
    ddl_dir = sys_dir / "sys_ddl"
    # Unified support DB. Mirrors loader_env.get_sys_db_path()
    # (USEKIT_PATH/sys/sys_db/usekit.db); here we build it from the explicit
    # project_path because ENV_BASE_PATH may not be settled yet during setup.
    db_path = sys_dir / "sys_db" / "usekit.db"
    ddl_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        print()
        print("[USEKIT TASK MANAGER]")

    # -- copy bundled seeds out of the (read-only) package --
    try:
        from usekit.classes.common.setup.helper_setup_config import _find_source_usekit
        source = _find_source_usekit()
    except Exception:
        source = None

    if source is not None:
        for src in sorted((source / _BUNDLE_DDL).glob("*.sql")):
            dst = ddl_dir / src.name
            if dst.resolve() == src.resolve() or dst.exists():
                continue          # dev mode (same file) or already copied
            try:
                shutil.copy2(str(src), str(dst))
            except Exception as e:
                if verbose:
                    print(f"  [WARN] seed copy failed ({src.name}): {e}")

    seeds = sorted(ddl_dir.glob("*.sql"))
    if not seeds:
        if verbose:
            print("  [WARN] no seed DDL found.")
        return False

    # -- load into usekit.db (plain sqlite3 -- no extra deps, explicit path) --
    con = sqlite3.connect(str(db_path))
    try:
        for f in seeds:
            con.executescript(f.read_text(encoding="utf-8"))
        con.commit()
        # Explicit expected-table check (not TSK_% LIKE) so meta tables count too.
        expected = [
            "TSK_TASK", "TSK_STEP", "TSK_SESSION", "TSK_MESSAGE", "TSK_CONTEXT",
            "SYS_META", "TBL_META", "TSK_META", "TSK_CALL",
        ]
        # CREATE TABLE IF NOT EXISTS never alters a table that already exists, so a
        # column added to the seed DDL in a later release would never reach a
        # pre-existing usekit.db. That is exactly how TSK_SESSION.slot went
        # missing -> create_session() raised "no such column: slot" -> sessions
        # were never persisted (turns stranded in TSK_MESSAGE with no parent).
        # Reconcile against the DDL and ALTER-in the missing columns.
        _migrate_add_missing_columns(con, seeds, expected, verbose)
        have = {
            r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        tables = [t for t in expected if t in have]
        missing = [t for t in expected if t not in have]
    finally:
        con.close()

    if verbose:
        if missing:
            print(f"  [WARN] missing tables: {', '.join(missing)}")
        if tables:
            print(f"  usekit.db ready: {len(tables)} tables ({', '.join(tables)})")
            print("Task manager ready.")
        else:
            print("  [WARN] no expected tables created.")
    return not missing


def _is_const_default(dflt) -> bool:
    """True if a PRAGMA default is a literal SQLite can apply on ADD COLUMN.

    SQLite rejects non-constant defaults (e.g. datetime('now')) on
    ALTER TABLE ADD COLUMN, so only numbers, quoted strings and NULL/bool
    literals qualify.
    """
    if dflt is None:
        return False
    s = str(dflt).strip()
    if not s:
        return False
    if s.upper() in ("NULL", "TRUE", "FALSE"):
        return True
    if (s[0] == "'" and s[-1] == "'") or (s[0] == '"' and s[-1] == '"'):
        return True
    try:
        float(s)
        return True
    except ValueError:
        return False


def _migrate_add_missing_columns(con, seeds, expected, verbose: bool = True):
    """Add columns present in the seed DDL but missing from an existing table.

    DDL is the source of truth: build a throwaway in-memory DB from the same
    seeds, read each table's intended columns, and ALTER TABLE ADD COLUMN the
    ones the live DB lacks. Idempotent and conservative -- only NULL-able or
    constant-default columns are added; a NOT NULL column without a constant
    default is reported for manual migration rather than guessed at. Failures
    are surfaced, never swallowed (P1-3).
    """
    import sqlite3

    ref = sqlite3.connect(":memory:")
    try:
        for f in seeds:
            ref.executescript(f.read_text(encoding="utf-8"))
        for table in expected:
            try:
                want = ref.execute(f"PRAGMA table_info({table})").fetchall()
            except sqlite3.OperationalError:
                continue  # table absent from DDL ref -> nothing to mirror
            if not want:
                continue
            have_cols = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
            if not have_cols:
                continue  # table missing entirely -> CREATE handles it, not ALTER
            for _cid, name, ctype, notnull, dflt, _pk in want:
                if name in have_cols:
                    continue
                const_dflt = _is_const_default(dflt)
                if notnull and not const_dflt:
                    if verbose:
                        print(f"  [WARN] cannot auto-add {table}.{name} "
                              f"(NOT NULL without constant default) -- manual migration needed")
                    continue
                clause = f'ALTER TABLE {table} ADD COLUMN "{name}" {ctype or ""}'.rstrip()
                if const_dflt:
                    clause += (f" NOT NULL DEFAULT {dflt}" if notnull else f" DEFAULT {dflt}")
                try:
                    con.execute(clause)
                    if verbose:
                        print(f"  [MIGRATE] {table}.{name} added")
                except sqlite3.OperationalError as e:
                    print(f"  [WARN] migrate {table}.{name} failed: {e}")  # surfaced (P1-3)
        con.commit()
    finally:
        ref.close()


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
