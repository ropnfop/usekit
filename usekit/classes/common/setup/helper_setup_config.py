# Path: usekit.classes.common.setup.helper_setup_config
# -----------------------------------------------------------------------------------------------
# Config writing and editor options for use.setup()
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


# Default editor config
_EDITOR_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 7979,
    "auto_bash": False,
    "autostart": False,
    "task_manage": False,
}


def ask_editor_options(verbose: bool = True) -> Dict:
    """
    Ask user for editor behavior settings.
    
    Returns:
        dict with host, port, auto_bash, autostart keys
    """
    config = _EDITOR_DEFAULTS.copy()

    if verbose:
        print()

    try:
        answer = input("Enable auto bash command handling? [y/N]: ").strip().lower()
        config["auto_bash"] = answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        pass

    status = "enabled" if config["auto_bash"] else "disabled"
    if verbose:
        print(f"Auto bash handling {status}.")

    try:
        answer = input("Auto-start editor on Termux launch? [y/N]: ").strip().lower()
        config["autostart"] = answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        pass

    status = "enabled" if config["autostart"] else "disabled"
    if verbose:
        print(f"Editor autostart {status}.")

    try:
        answer = input("Enable task manager (usekit.db + Claude Code task tracking)? [y/N]: ").strip().lower()
        config["task_manage"] = answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        pass

    status = "enabled" if config["task_manage"] else "disabled"
    if verbose:
        print(f"Task manager {status}.")

    return config


def create_project_structure(project_path: Path, verbose: bool = True) -> bool:
    """
    Create project directory structure.
    
    Creates:
        project_path/
          usekit/
            sys/
              sys_yaml/
            .env
          _tmp/
          data/
    """
    dirs = [
        project_path / ".usekit" / "sys" / "sys_yaml",
        project_path / ".usekit" / "sys" / "sys_json",
        project_path / ".usekit" / "sys" / "sys_km",
        project_path / ".usekit" / "sys" / "sys_db",
        project_path / ".usekit" / "sys" / "sys_ddl",
        project_path / "_tmp",
        project_path / "data",
    ]

    try:
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        if verbose:
            print()
            print("Creating project structure...")
            print()
            print(f"  {project_path.name}/")
            print(f"    usekit/")
            print(f"      sys/")
            print(f"        sys_yaml/")
            print(f"    _tmp/")
            print(f"    data/")

        return True
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to create directories: {e}")
        return False


def build_sys_project_data(
    project_name: str,
    editor_config: Dict,
) -> Dict:
    """Build the sys_project.yaml data dict."""
    today = datetime.now().strftime("%Y-%m-%d")

    return {
        "project": {
            "name": project_name,
        },
        "editor": {
            "host": editor_config.get("host", _EDITOR_DEFAULTS["host"]),
            "port": editor_config.get("port", _EDITOR_DEFAULTS["port"]),
            "auto_bash": editor_config.get("auto_bash", _EDITOR_DEFAULTS["auto_bash"]),
            "task_manage": editor_config.get("task_manage", _EDITOR_DEFAULTS["task_manage"]),
        },
        "created": today,
        "updated": today,
    }


def write_sys_project(
    project_path: Path,
    data: Dict,
    verbose: bool = True,
) -> bool:
    """
    Write sys_project.yaml to project's sys_yaml folder.
    Also updates the central cache via helper_const.
    """
    yaml_dir = project_path / ".usekit" / "sys" / "sys_yaml"
    yaml_path = yaml_dir / "sys_project.yaml"

    try:
        import yaml

        yaml_dir.mkdir(parents=True, exist_ok=True)
        with yaml_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                data, f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        if verbose:
            print()
            print(f"Config saved:")
            print(f"  {yaml_path}")

        # Update central cache
        try:
            from usekit.classes.common.utils.helper_const import (
                save_sys_project,
                clear_sys_project_cache,
            )
            clear_sys_project_cache()
            save_sys_project(data)
        except ImportError:
            pass

        return True

    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to write config: {e}")
        return False


def _find_source_usekit() -> Optional[Path]:
    """Find the source usekit package directory. Returns None on failure."""
    # Method 1: usekit.__file__
    try:
        import usekit
        f = getattr(usekit, '__file__', None)
        if f is not None:
            p = Path(f).parent
            if p.exists():
                return p
    except Exception:
        pass

    # Method 2: importlib.resources
    try:
        from importlib.resources import files
        p = Path(str(files("usekit")))
        if p.exists():
            return p
    except Exception:
        pass

    # Method 3: search site-packages
    try:
        import site
        for sp in site.getsitepackages():
            cand = Path(sp) / "usekit"
            if (cand / "__init__.py").exists():
                return cand
    except Exception:
        pass

    return None


def _generate_sys_const_yaml() -> str:
    """Generate sys_const.yaml with full default content for new projects."""
    return '''\
# Path: usekit.sys.sys_yaml.sys_const.yaml
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# -----------------------------------------------------------------------------------------------
# Note: BASE_PATH and USEKIT_PATH are auto-calculated from .env (ENV_BASE_PATH).
#       No hardcoded paths are needed. They are injected at runtime by loader_env.py.
# -----------------------------------------------------------------------------------------------

# USEKIT
SYS_PATH:
  root: "usekit/sys"
  json: "sys_json"
  yaml: "sys_yaml"
  db: "sys_db"
  ddl: "sys_ddl"

# ────────────────────────────────────────────────
# [USE ZONE: Basic - fixed] use.read.json() / use.read.json.sub()
# ────────────────────────────────────────────────

# DB: Database
DB_PATH:
  root: "data/table/db"
  db: "base.db"
  db_sub: "sub.db"

# DDL: Data Definition Language
DDL_PATH:
  root: "data/table/ddl"
  ddl: "base"
  ddl_sub: "sub"

# SQL: Data Manipulation / Query files
SQL_PATH:
  root: "data/table/sql"
  sql: "base"
  sql_sub: "sub"

# PYP: Python module files
PYP_PATH:
  root: "src"
  py: "base"
  py_sub: "sub"
  pyp: "base"
  pyp_sub: "sub"

# ────────────────────────────────────────────────
# [DATA: Per-format paths]
# Each format has its own root.
# Subkeys keep their existing names, such as json, json_sub, and so on.
# ────────────────────────────────────────────────

# JSON
JSON_PATH:
  root: "data/json"
  json: "base"
  json_sub: "sub"

# YAML
YAML_PATH:
  root: "data/yaml"
  yaml: "base"
  yaml_sub: "sub"

# LOG
LOG_PATH:
  root: "data/log"
  log: "base"
  log_sub: "sub"

# MD
MD_PATH:
  root: "docs"
  md: "base"
  md_sub: "sub"

# TXT
TXT_PATH:
  root: "data/common/txt"
  txt: "base"
  txt_sub: "sub"

# CSV
CSV_PATH:
  root: "data/common/csv"
  csv: "base"
  csv_sub: "sub"

# ANY: Generic data zone
ANY_PATH:
  root: "data/common/any"
  any: "base"
  any_sub: "sub"

# KM
KM_PATH:
  root: "data/any/km"
  km: "base"
  km_sub: "sub"

# PKL: Runtime cache
PKL_PATH:
  root: "data"
  pkl: ".runtime_cache"

# TMP: Temporary files
TMP_PATH:
  root: "data"
  txt: "tmp"
  md: "tmp"
  py: "tmp"
  pyp: "tmp"
  json: "tmp"
  yaml: "tmp"
  ddl: "tmp"
  sql: "tmp"
  km: "tmp"
  any: "tmp"

# CUS: Custom user-defined paths
CUS_PATH:
  root: "/"
  tests: "tests"
  backup: "backup"
  custom: "data/custom"

# ────────────────────────────────────────────────
# [DATA Formats]
# fmt: any, mod: any  → the final location is determined by loc.
# fmt: any, mod: txt  → fmt is overridden as txt.
# ────────────────────────────────────────────────

# Section mapping for path generation.
# Used by help_path.py.
FORMAT_SECTION_MAP:
  any: ANY_PATH
  tmp: TMP_PATH
  pkl: PKL_PATH
  cus: CUS_PATH

  json: JSON_PATH
  yaml: YAML_PATH
  txt: TXT_PATH
  csv: CSV_PATH
  md: MD_PATH
  log: LOG_PATH

  ddl: DDL_PATH
  sql: SQL_PATH
  py: PYP_PATH
  pyp: PYP_PATH
  km: KM_PATH

# Extension handling for the any format is handled in help_format.py.
# Only formats with function support, such as use.read.json.base(), are mapped here.
EXTENSION_MAP:
  json: ".json"
  yaml: ".yaml"
  ddl: ".sql"
  sql: ".sql"
  txt: ".txt"
  log: ".log"
  csv: ".csv"
  md: ".md"
  pyp: ".py"
  py: ".py"
  pkl: ".pkl"
  km: ".km"
  any: ".txt"

# [USE ZONE END]

# ────────────────────────────────────────────────
# [TIME]
# ────────────────────────────────────────────────
TIME:
  default_tz: "local"
# default_tz: "Asia/Seoul"

# Language: "kr" for Korean help, "en" for English help. Default: en.
LANG: "en"

# ────────────────────────────────────────────────
# [EXT: Extension paths] use.read.json.[userfolder]()
# ────────────────────────────────────────────────
DB_EXT_PATH:
  root: "data/db"
  db01: "ext_db01.db"
  db02: "ext_db02.db"

DML_EXT_PATH:
  root: "data/tables/ext"
  dml01: "dml01"
  dml02: "dml02"

MOD_EXT_PATH:
  root: "main/module"
  mod01: "sub01"
  mod02: "sub02"

DATA_EXT_PATH:
  root: "data"
  json: "json"
  json01: "json"
  yaml01: "yaml/yaml01"
  txt01: "common/files"
  csv01: "common/files"
  md01: "common/files"

# ────────────────────────────────────────────────
# [DSL] dsl.set("format", "folder_name", dir_path) / dsl.get()
# ────────────────────────────────────────────────
DSL_PATH:
  json:
    temp: "/tmp/json/"
  yaml:
    temp: "/tmp/yaml/"
  txt:
    temp: "/tmp/txt/"
  csv:
    temp: "/tmp/csv/"

# ────────────────────────────────────────────────
# [DEBUG]
# ────────────────────────────────────────────────
DEBUG: true
DEBUG_OPTIONS:
  timer: false
  loader: false
  helper: false
  safer: false
  helperext: false
  pyp: false
  json: false
  yaml: false
  ddl: false
  sql: false
  txt: false
  md: false
  csv: false
  pkl: false
  log: false
  km: false
  any: false

# ────────────────────────────────────────────────
# [MODEL]
# ────────────────────────────────────────────────
USE_VERTEX: false
VERTEX_ID: "vertex-ai-demo"
GCP_ID: "vertex-ai-demo"
GCP_LOCATION: "us-central1"

MODEL:
  default: G15F
  mapping:
    BISON: "text-bison-001"
    CLAUDE: "claude-3-opus-20240229"
    G15F: "gemini-1.5-flash"
    G15P: "gemini-1.5-pro"
    G20F: "gemini-2.0-flash"
    G20L: "gemini-2.0-flash-lite"
    G20P: "gemini-2.0-pro"
    G20PR: "gemini-2.0-pro-vision"
    GPT35: "gpt-3.5-turbo"
    GPT4: "gpt-4"
    GPT4V: "gpt-4-vision-preview"
    LLAMA38: "meta-llama/Meta-Llama-3-8B"
    LLAMA370: "meta-llama/Meta-Llama-3-70B"
    MIXTRAL: "mistralai/Mixtral-8x7B-Instruct-v0.1"
    PALM2: "palm-2-chat-bison"
    WHISPER: "openai/whisper-large-v3"

    # GEMMA
    # Relative paths are resolved from BASE_PATH.
    GEM3-4B-IT: "gemma/gemma-3-4b-it"
    GEM3-1B-IT: "gemma/gemma-3-1b-it"
    GEM3-270M-IT: "gemma/gemma-3-270m-it"
'''


def _generate_project_meta_md() -> str:
    """Built-in default for project_meta.md (system-prompt project identity).

    USEKIT is a PyPI library, so every install has a different project/domain.
    The default is intentionally minimal and generic: only what is true for any
    USEKIT install (library base, non-exposure, language). Concrete project/user
    details are filled per-install via the editor META cards. Runtime values
    (date/provider/slot/session) are injected at call time, not stored here.
    """
    return '''\
# USEKIT Project Meta

## Project [on]

Built on USEKIT. Keep internal system processing private; never expose it.

## User [on]

Do not assume or state the user's identity. Reply in Korean.

## Meta [on]

- Korean replies.
- English code/comments/identifiers.

## Request [off]

Apply the user's latest instruction to the current task.
'''


def _generate_env_content(project_path, project_name: str = "pj01") -> str:
    """Generate full .env content with ENV_BASE_PATH set."""
    return f'''\
# USEKIT Environment Configuration
# ================================================================================
# This file is automatically used to create .env with smart path binding
# Copy this to .env and adjust values as needed
# ================================================================================

# ────────────────────────────────────────────────────────────────────────────
# [REQUIRED] Base project path - Auto-detected by environment
# ────────────────────────────────────────────────────────────────────────────
# USEKIT will automatically set this based on your environment:
#
# Termux (Android):  /storage/emulated/0/projects/pj01
# Google Colab:      /content/drive/MyDrive/PROJECT
# Local Dev:         Detected from usekit package location
# Pip Install:       You MUST set this manually
#
# Override auto-detection by uncommenting and setting manually:
ENV_BASE_PATH={project_path}
ENV_PROJECT={project_name}

# ────────────────────────────────────────────────────────────────────────────
# [OPTIONAL] API Keys & Services
# ────────────────────────────────────────────────────────────────────────────
# Add your API keys here (these will be masked in logs)

# OpenAI API
# OPENAI_API_KEY=sk-your-key-here

# Anthropic Claude API
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# Google APIs
# GOOGLE_API_KEY=your-key-here

# Other services
# PINECONE_API_KEY=your-key-here
# LANGCHAIN_API_KEY=your-key-here

# ────────────────────────────────────────────────────────────────────────────
# [OPTIONAL] Database Configuration
# ────────────────────────────────────────────────────────────────────────────
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=mydb
# DB_USER=user
# DB_PASSWORD=password

# ────────────────────────────────────────────────────────────────────────────
# [OPTIONAL] Application Settings
# ────────────────────────────────────────────────────────────────────────────
# DEBUG=false
# LOG_LEVEL=INFO
# TIMEZONE=Asia/Seoul

# ────────────────────────────────────────────────────────────────────────────
# Platform-Specific Notes
# ────────────────────────────────────────────────────────────────────────────
#
# TERMUX USERS:
# - Default path: /storage/emulated/0/projects/pj01
# - This directory will be auto-created if it doesn't exist
# - Make sure Termux has storage permission: run 'termux-setup-storage'
# - Alternative path: ~/u_project (inside Termux home)
#
# GOOGLE COLAB USERS:
# - Mount Google Drive first: from google.colab import drive; drive.mount('/content/drive')
# - Default path: /content/drive/MyDrive/PROJECT
# - Will fallback to /content if Drive not mounted
#
# LOCAL DEVELOPMENT:
# - Path is auto-detected from usekit package location
# - Typically: /path/to/your/project (where usekit/ folder exists)
#
# PIP INSTALLED:
# - ENV_BASE_PATH is REQUIRED and must be set manually
# - Choose a location for your project files
# - Example: ENV_BASE_PATH=/home/user/myproject
#
# ────────────────────────────────────────────────────────────────────────────
# End of configuration
# ────────────────────────────────────────────────────────────────────────────
'''


def copy_source_configs(project_path: Path, project_name: str, verbose: bool = True) -> bool:
    """
    Copy .env.example → .env (with path update) and sys_const.yaml from source.
    Falls back to generating files directly if source package is inaccessible.
    Skips files that already exist in target.
    """
    source = _find_source_usekit()  # may be None
    success = True

    # ── .env ──
    env_dst = project_path / ".usekit" / ".env"

    if env_dst.exists():
        if verbose:
            print(f"  .env already exists, skipping.")
    else:
        written = False
        # Try copying from source .env.example
        if source is not None:
            env_src = source / ".env.example"
            if env_src.exists():
                try:
                    content = env_src.read_text(encoding="utf-8")
                    import re
                    content = re.sub(
                        r'^#?\s*ENV_BASE_PATH=.*$',
                        f'ENV_BASE_PATH={project_path}',
                        content,
                        flags=re.MULTILINE,
                    )
                    if f"ENV_BASE_PATH={project_path}" not in content:
                        content += f"\nENV_BASE_PATH={project_path}\n"
                    # Ensure ENV_PROJECT is set
                    if "ENV_PROJECT=" not in content:
                        content += f"ENV_PROJECT={project_name}\n"
                    env_dst.parent.mkdir(parents=True, exist_ok=True)
                    env_dst.write_text(content, encoding="utf-8")
                    written = True
                    if verbose:
                        print(f"  Copied: .env.example → .env")
                except Exception as e:
                    if verbose:
                        print(f"  [WARN] .env copy failed: {e}")

        # Fallback: create full .env from built-in template
        if not written:
            try:
                content = _generate_env_content(project_path, project_name)
                env_dst.parent.mkdir(parents=True, exist_ok=True)
                env_dst.write_text(content, encoding="utf-8")
                if verbose:
                    print(f"  Created: .env (built-in)")
            except Exception as e:
                if verbose:
                    print(f"  [WARN] .env creation failed: {e}")
                success = False

    # ── sys_const.yaml ──
    const_dst = project_path / ".usekit" / "sys" / "sys_yaml" / "sys_const.yaml"

    if const_dst.exists():
        if verbose:
            print(f"  sys_const.yaml already exists, skipping.")
    else:
        copied = False
        # Try copying from source
        if source is not None:
            const_src = source / "sys" / "sys_yaml" / "sys_const.yaml"
            if const_src.exists():
                try:
                    import shutil
                    const_dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(const_src), str(const_dst))
                    copied = True
                    if verbose:
                        print(f"  Copied: sys_const.yaml")
                except Exception as e:
                    if verbose:
                        print(f"  [WARN] sys_const.yaml copy failed: {e}")

        # Fallback: generate sys_const.yaml directly
        if not copied:
            try:
                const_dst.parent.mkdir(parents=True, exist_ok=True)
                const_dst.write_text(_generate_sys_const_yaml(), encoding="utf-8")
                if verbose:
                    print(f"  Generated: sys_const.yaml (built-in)")
            except Exception as e:
                if verbose:
                    print(f"  [WARN] sys_const.yaml generation failed: {e}")
                success = False

    # ── project_meta.md (project base meta → system prompt) ──
    # Persistent project identity/rules injected via _config["system"] on conn
    # (project_meta=True). Same copy-or-generate pattern as sys_const.yaml.
    # Preserved if it already exists (user edits win).
    meta_dst = project_path / ".usekit" / "sys" / "sys_yaml" / "project_meta.md"
    if meta_dst.exists():
        if verbose:
            print(f"  project_meta.md already exists, skipping.")
    else:
        meta_copied = False
        if source is not None:
            meta_src = source / "sys" / "sys_yaml" / "project_meta.md"
            if meta_src.exists():
                try:
                    import shutil
                    meta_dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(meta_src), str(meta_dst))
                    meta_copied = True
                    if verbose:
                        print(f"  Copied: project_meta.md")
                except Exception as e:
                    if verbose:
                        print(f"  [WARN] project_meta.md copy failed: {e}")
        if not meta_copied:
            try:
                meta_dst.parent.mkdir(parents=True, exist_ok=True)
                meta_dst.write_text(_generate_project_meta_md(), encoding="utf-8")
                if verbose:
                    print(f"  Generated: project_meta.md (built-in)")
            except Exception as e:
                if verbose:
                    print(f"  [WARN] project_meta.md generation failed: {e}")

    # ── project_meta.default.md (immutable Reset baseline) ──
    # Same content as the active copy initially. "Reset Default" reads from this
    # file, and auto-save never touches it, so the working copy can always be
    # reset back to it. Users may customize this file as their own default.
    # Preserved if it already exists.
    meta_def_dst = project_path / ".usekit" / "sys" / "sys_yaml" / "project_meta.default.md"
    if meta_def_dst.exists():
        if verbose:
            print(f"  project_meta.default.md already exists, skipping.")
    else:
        def_copied = False
        if source is not None:
            meta_src = source / "sys" / "sys_yaml" / "project_meta.md"
            if meta_src.exists():
                try:
                    import shutil
                    meta_def_dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(meta_src), str(meta_def_dst))
                    def_copied = True
                    if verbose:
                        print(f"  Copied: project_meta.default.md")
                except Exception as e:
                    if verbose:
                        print(f"  [WARN] project_meta.default.md copy failed: {e}")
        if not def_copied:
            try:
                meta_def_dst.parent.mkdir(parents=True, exist_ok=True)
                meta_def_dst.write_text(_generate_project_meta_md(), encoding="utf-8")
                if verbose:
                    print(f"  Generated: project_meta.default.md (built-in)")
            except Exception as e:
                if verbose:
                    print(f"  [WARN] project_meta.default.md generation failed: {e}")

    # ── Load new .env into current process ──
    if env_dst.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_dst, override=True)
        except Exception:
            pass

    return success
