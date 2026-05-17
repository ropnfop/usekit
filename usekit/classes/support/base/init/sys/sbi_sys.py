# Path: usekit.classes.support.base.init.sys.sbi_sys.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# — memory is emotion —
# -----------------------------------------------------------------------------------------------
# Purpose:
#   System support handler (us) — thin wrapper over existing usekit infra.
#   No duplicate logic. Delegates to loader_env, helper_const, etc.
#
#   .env is already loaded by usekit/__init__.py → load_env().
#   us just provides a clean access layer + key masking.
#
#   Usage:
#       from usekit import us
#       us.key("ANTHROPIC_API_KEY")       # get API key
#       us.keys()                         # list all keys (masked)
#       us.base()                         # BASE_PATH
#       us.platform()                     # 'termux' | 'colab' | 'pip' | 'local'
#       us.debug()                        # print system info
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional


# ========================================================================
# Internal: Key masking
# ========================================================================

_SENSITIVE = ("KEY", "SECRET", "TOKEN", "PASSWORD", "PASS", "API")


def _mask(val: str, show: int = 3) -> str:
    """Mask a sensitive value, showing only first/last N chars."""
    if not val:
        return ""
    if len(val) <= show * 2:
        return "***"
    return f"{val[:show]}...{val[-show:]}"


def _is_sensitive(key: str) -> bool:
    """Check if an env key looks sensitive."""
    upper = key.upper()
    return any(pat in upper for pat in _SENSITIVE)


# ========================================================================
# SysHandler — the us object
# ========================================================================

class SysHandler:
    """
    System support handler for usekit.
    Thin wrapper — no duplicate logic, delegates to existing infra.
    """

    # ── Environment ──────────────────────────────────────────

    def env(self, force: bool = False, verbose: bool = True) -> bool:
        """
        Load .env file (delegates to loader_env).

        Example:
            us.env()                  # reload
            us.env(force=True)        # force reload
        """
        try:
            from usekit.classes.core.env.loader_env import load_env
            result = load_env(force=force, verbose=verbose)
            return result is not None
        except Exception as e:
            if verbose:
                print(f"[us] env load failed: {e}")
            return False

    def key(self, name: str, value: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
        """
        Get or set an environment variable.
        1 arg  → read from os.environ
        2 args → write to .env file + os.environ

        Example:
            us.key("ANTHROPIC_API_KEY")                  # read
            us.key("ANTHROPIC_API_KEY", "sk-ant-xxx")    # write to .env
            us.key("MY_KEY", default="fallback")         # read with fallback
        """
        if value is not None:
            # Write mode: save to .env + os.environ
            from usekit.classes.common.utils.helper_env import set_env
            set_env(name, value)
            return value
        # Read mode
        return os.getenv(name, default)

    def delkey(self, name: str) -> bool:
        """
        Remove a key from .env file and os.environ.

        Example:
            us.delkey("OLD_API_KEY")
        """
        from usekit.classes.common.utils.helper_env import del_env
        return del_env(name)

    def keys(self, mask: bool = True, filter_sensitive: bool = False) -> Dict[str, str]:
        """
        Get environment variables with optional masking.

        Example:
            us.keys()                     # all, masked
            us.keys(mask=False)           # all, raw
            us.keys(filter_sensitive=True) # only secrets
        """
        result = {}
        for k, v in os.environ.items():
            sensitive = _is_sensitive(k)
            if filter_sensitive and not sensitive:
                continue
            if mask and sensitive:
                result[k] = _mask(v)
            else:
                result[k] = v
        return result

    def set(self, name: str, value: str):
        """
        Set an environment variable (runtime only).

        Example:
            us.set("MY_VAR", "hello")
        """
        os.environ[name] = str(value)

    def has(self, name: str) -> bool:
        """
        Check if an environment variable exists.

        Example:
            if us.has("ANTHROPIC_API_KEY"): ...
        """
        return name in os.environ

    # ── Paths (delegate to helper_const) ─────────────────────

    def base(self) -> Path:
        """
        Get project BASE_PATH.

        Example:
            us.base()  # → Path('/storage/emulated/0/projects/pj01')
        """
        try:
            from usekit.classes.common.utils.helper_const import get_base_path
            return get_base_path()
        except Exception:
            env_base = os.getenv("ENV_BASE_PATH")
            return Path(env_base) if env_base else Path.cwd()

    def project(self, name: Optional[str] = None) -> str:
        """
        Get or rename current project.

        Read:  us.project()           → 'pj01'
        Write: us.project("test01")   → renames pj01/ → test01/, updates .env + yaml

        Read order:
            1. sys_project.yaml → project.name
            2. Fallback: folder name from base path

        Example:
            us.project()              # → 'pj01'
            us.project("test01")      # → 'test01' (renamed)
        """
        import shutil

        base = self.base()

        if name is None:
            # Read from sys_project.yaml first
            try:
                from usekit.classes.common.utils.helper_const import get_project_value
                yaml_name = get_project_value("project.name")
                if yaml_name:
                    return yaml_name
            except ImportError:
                pass
            # Fallback: folder name
            return base.name

        # Same name — nothing to do
        if base.name == name:
            return name

        new_base = base.parent / name

        # Safety: target must not already exist
        if new_base.exists():
            raise FileExistsError(
                f"Target already exists: {new_base}\n"
                f"Cannot rename '{base.name}' → '{name}'"
            )

        # Rename the project folder
        try:
            base.rename(new_base)
        except OSError:
            # Cross-device rename: copy + remove
            shutil.copytree(str(base), str(new_base))
            shutil.rmtree(str(base))

        # Update .env inside the renamed folder
        env_file = new_base / "usekit" / ".env"
        if env_file.exists():
            self._update_env_file(env_file, {
                "ENV_BASE_PATH": str(new_base),
                "ENV_PROJECT": name,
            })

        # Update sys_project.yaml
        self._update_sys_project_name(new_base, name)

        # Sync os.environ
        os.environ["ENV_BASE_PATH"] = str(new_base)
        os.environ["ENV_PROJECT"] = name

        # Clear all caches
        self._clear_path_caches()

        print(f"[us] Renamed: {base.name} → {name}")
        print(f"[us] Path: {new_base}")

        return name

    def _update_sys_project_name(self, project_path: Path, name: str):
        """Update project.name in sys_project.yaml after rename."""
        from datetime import datetime
        yaml_path = project_path / "usekit" / "sys" / "sys_yaml" / "sys_project.yaml"
        if not yaml_path.exists():
            return
        try:
            import yaml
            with yaml_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if "project" not in data:
                data["project"] = {}
            data["project"]["name"] = name
            data["updated"] = datetime.now().strftime("%Y-%m-%d")
            with yaml_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False,
                               allow_unicode=True, sort_keys=False)
            # Clear yaml cache
            from usekit.classes.common.utils.helper_const import clear_sys_project_cache
            clear_sys_project_cache()
        except Exception:
            pass

    def project_config(self, key: Optional[str] = None):
        """
        Read sys_project.yaml values.

        us.project_config()              → full dict
        us.project_config("editor.port") → 7979
        """
        try:
            if key is None:
                from usekit.classes.common.utils.helper_const import get_sys_project
                return get_sys_project()
            from usekit.classes.common.utils.helper_const import get_project_value
            return get_project_value(key)
        except ImportError:
            return {} if key is None else None

    def _update_env_file(self, env_file: Path, updates: dict):
        """Update key=value pairs in a .env file directly."""
        try:
            from usekit.classes.core.env.base.manager_dotenv import update_env_variable
            for key, value in updates.items():
                update_env_variable(env_file, key, value)
        except Exception:
            # Fallback: manual rewrite
            lines = env_file.read_text(encoding="utf-8").splitlines()
            result = []
            updated_keys = set()
            for line in lines:
                stripped = line.strip()
                matched = False
                for key, value in updates.items():
                    if stripped.startswith(f"{key}="):
                        result.append(f"{key}={value}")
                        updated_keys.add(key)
                        matched = True
                        break
                if not matched:
                    result.append(line)
            # Append any keys not found
            for key, value in updates.items():
                if key not in updated_keys:
                    result.append(f"{key}={value}")
            env_file.write_text("\n".join(result) + "\n", encoding="utf-8")

    def _clear_path_caches(self):
        """Reset ALL path caches after project switch."""
        # 1. loader_env — project root, base path, env dict, etc.
        try:
            from usekit.classes.core.env import loader_env
            loader_env.clear_all_caches()
        except Exception:
            pass
        # 2. loader_base_path — _BASE_PATH_CACHE (used by BASE_PATH proxy)
        try:
            from usekit.classes.core.env import loader_base_path
            loader_base_path.clear_base_path_cache()
        except Exception:
            pass
        # 3. helper_const — _BASE_PATH_CACHE + sys_const lru_cache
        try:
            from usekit.classes.common.utils import helper_const
            helper_const._BASE_PATH_CACHE = None
            if hasattr(helper_const, 'clear_sys_const_cache'):
                helper_const.clear_sys_const_cache()
            # Clear any lru_cache on get_const
            if hasattr(helper_const, 'get_const') and hasattr(helper_const.get_const, 'cache_clear'):
                helper_const.get_const.cache_clear()
        except Exception:
            pass
        # 4. helper_env — .env path cache
        try:
            from usekit.classes.common.utils import helper_env
            helper_env.clear_cache()
        except Exception:
            pass

    def join(self, *parts: str) -> str:
        """
        Join path parts.

        Example:
            us.join("data", "json", "config.json")
        """
        return str(Path(*parts))

    def exists(self, path: str) -> bool:
        """
        Check if a file or directory exists.

        Example:
            us.exists("data/config.json")
        """
        return Path(path).exists()

    def mkdir(self, path: str, parents: bool = True, exist_ok: bool = True):
        """
        Create a directory.

        Example:
            us.mkdir("output/reports")
        """
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def rmdir(self, path: str):
        """
        Remove a directory and all contents.

        Example:
            us.rmdir("tmp/cache")
        """
        import shutil
        p = Path(path)
        if p.exists():
            shutil.rmtree(p)

    def abs(self, path: str) -> str:
        """
        Convert to absolute path.

        Example:
            us.abs("data/config.json")
        """
        return str(Path(path).resolve())

    # ── Platform (delegate to loader_env) ────────────────────

    def is_termux(self) -> bool:
        """Check if running in Termux."""
        try:
            from usekit.classes.core.env.loader_env import is_termux
            return is_termux()
        except Exception:
            return bool(os.getenv("TERMUX_VERSION"))

    def is_colab(self) -> bool:
        """Check if running in Google Colab."""
        try:
            from usekit.classes.core.env.loader_env import is_colab
            return is_colab()
        except Exception:
            try:
                import google.colab  # noqa
                return True
            except ImportError:
                return False

    def is_pip(self) -> bool:
        """Check if usekit is pip-installed."""
        try:
            from usekit.classes.core.env.loader_env import is_pip_env
            return is_pip_env()
        except Exception:
            return "site-packages" in str(Path(__file__).resolve())

    def platform(self) -> str:
        """
        Get current platform name.

        Returns:
            'termux', 'colab', 'pip', or 'local'

        Example:
            us.platform()  # → 'termux'
        """
        if self.is_termux():
            return "termux"
        if self.is_colab():
            return "colab"
        if self.is_pip():
            return "pip"
        return "local"

    # ── Config (delegate to helper_const) ────────────────────

    def const(self, key: str, default: Any = None) -> Any:
        """
        Get value from sys_const.yaml (dot notation).

        Example:
            us.const("TIME.default_tz")
            us.const("DATA_PATH.json")
        """
        try:
            from usekit.classes.common.utils.helper_const import get_const
            return get_const(key)
        except Exception:
            return default

    # ── AI system manager (us.ai) — excluded from public release ──

    @property
    def ai(self):
        """AI module is not included in this release."""
        raise AttributeError(
            "us.ai is not available in this release. "
            "AI module will be included in a future version."
        )

    # ── Debug ────────────────────────────────────────────────

    def info(self) -> Dict[str, str]:
        """
        Debug info: all detected paths and platform.

        Example:
            us.info()
        """
        env_file = "(unknown)"
        try:
            from usekit.classes.core.env.loader_env import find_env_file
            ef = find_env_file(auto_copy=False)
            env_file = str(ef) if ef else "(not found)"
        except Exception:
            pass

        return {
            "platform": self.platform(),
            "base_path": str(self.base()),
            "env_file": env_file,
            "is_termux": str(self.is_termux()),
            "is_colab": str(self.is_colab()),
            "is_pip": str(self.is_pip()),
        }

    def debug(self):
        """Print debug info to console."""
        info = self.info()
        print("=" * 60)
        print("  us — System Info")
        print("=" * 60)
        for k, v in info.items():
            print(f"  {k:15s}: {v}")
        print("=" * 60)


# ========================================================================
# Singleton instance
# ========================================================================

us = SysHandler()

__all__ = ["SysHandler", "us"]

# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
