# Path: usekit.classes.common.setup.helper_setup_env
# -----------------------------------------------------------------------------------------------
# Environment detection and dependency check for use.setup()
# -----------------------------------------------------------------------------------------------

import os
import sys
import shutil
import subprocess
import platform
from typing import Dict, Tuple


# Core packages (must be installed via pyproject.toml)
CORE_DEPS = ["yaml", "dotenv"]

# Optional Python packages for AI/API
OPTIONAL_DEPS = ["requests"]

# Import name → pip package name
_PIP_NAMES = {
    "yaml": "PyYAML",
    "dotenv": "python-dotenv",
    "requests": "requests",
}

# Claude Code npm package
_CLAUDE_CODE_PKG = "@anthropic-ai/claude-code@1.0.33"


def _detect_platform() -> str:
    """Detect current platform."""
    try:
        from usekit.classes.core.env.loader_env import is_termux, is_colab
        if is_termux():
            return "termux"
        if is_colab():
            return "colab"
    except ImportError:
        pass
    return "local"


def _check_import(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _check_dependencies() -> Tuple[Dict[str, bool], Dict[str, bool]]:
    core = {name: _check_import(name) for name in CORE_DEPS}
    optional = {name: _check_import(name) for name in OPTIONAL_DEPS}
    return core, optional


def _check_cmd(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def detect_environment(verbose: bool = True) -> Dict:
    env = {
        "platform": _detect_platform(),
        "python": platform.python_version(),
        "cwd": os.getcwd(),
    }
    if verbose:
        print()
        print("=" * 60)
        print("[USEKIT SETUP]")
        print("=" * 60)
        print()
        print("System environment:")
        print(f"  - Platform : {env['platform'].capitalize()}")
        print(f"  - Python   : {env['python']}")
        print(f"  - Current  : {env['cwd']}")
    return env


def check_dependencies(verbose: bool = True) -> Tuple[Dict[str, bool], Dict[str, bool]]:
    core, optional = _check_dependencies()
    node_ok = _check_cmd("node")
    claude_ok = _check_cmd("claude")

    if verbose:
        print()
        print("[USEKIT DEPENDENCIES]")
        print()
        print("Core:")
        for name, ok in core.items():
            display = _PIP_NAMES.get(name, name)
            print(f"  {display:<20}: {'OK' if ok else 'MISSING'}")

        print()
        print("Optional (AI/API):")
        for name, ok in optional.items():
            display = _PIP_NAMES.get(name, name)
            print(f"  {display:<20}: {'OK' if ok else 'not installed'}")

        print()
        print("Claude Code (Node.js):")
        print(f"  {'node':<20}: {'OK' if node_ok else 'not installed'}")
        print(f"  {'claude CLI':<20}: {'OK' if claude_ok else 'not installed'}")

        missing_core = [n for n, ok in core.items() if not ok]
        if missing_core:
            print()
            names = [_PIP_NAMES.get(m, m) for m in missing_core]
            print(f"  [WARN] Missing core: {', '.join(names)}")
            print(f"  Fix: pip install {' '.join(names)}")

    return core, optional


def install_optional_deps(optional: Dict[str, bool], verbose: bool = True) -> bool:
    """Prompt to install missing optional Python deps."""
    missing = [name for name, ok in optional.items() if not ok]
    if not missing:
        if verbose:
            print()
            print("All optional packages already installed.")
        return False

    print()
    pip_list = [_PIP_NAMES.get(m, m) for m in missing]
    print(f"Missing: {', '.join(pip_list)}")

    try:
        answer = input("Install optional packages (AI/API)? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if answer not in ("y", "yes"):
        if verbose:
            print("Skipped. Install later: pip install " + " ".join(pip_list))
        return False

    installed, failed = [], []
    for name in missing:
        pip_name = _PIP_NAMES.get(name, name)
        if verbose:
            print(f"  Installing {pip_name}...", end=" ", flush=True)
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name, "-q"],
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode == 0:
                installed.append(pip_name)
                if verbose: print("OK")
            else:
                failed.append(pip_name)
                if verbose:
                    print("FAILED")
                    err = r.stderr.strip().split("\n")[-1] if r.stderr else ""
                    if err: print(f"    {err}")
        except subprocess.TimeoutExpired:
            failed.append(pip_name)
            if verbose: print("TIMEOUT")
        except Exception as e:
            failed.append(pip_name)
            if verbose: print(f"ERROR: {e}")

    if verbose:
        print()
        if installed: print(f"  Installed: {', '.join(installed)}")
        if failed:
            print(f"  Failed: {', '.join(failed)}")
            print(f"  Retry: pip install {' '.join(failed)}")

    return len(installed) > 0


def install_claude_cli(env_platform: str, verbose: bool = True) -> bool:
    """
    Install Claude Code CLI: Node.js + npm + claude-code + ws + bridge.js.
    Handles the full chain.
    """
    cli_exists = _check_cmd("claude")

    if cli_exists:
        if verbose:
            print()
            print("Claude Code CLI already installed.")
        # Still check auth + bridge
        _copy_bridge(verbose=verbose)
        _authenticate_claude(verbose=verbose)
        return True

    print()
    try:
        answer = input("Setup Claude Code? (Node.js + CLI + bridge) [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if answer not in ("y", "yes"):
        if verbose:
            print("Skipped.")
        return False

    # ── Step 1: Node.js ──
    if not _check_cmd("node"):
        if env_platform == "termux":
            if verbose:
                print("  Installing Node.js (pkg install nodejs-lts)...", flush=True)
            try:
                r = subprocess.run(
                    ["pkg", "install", "-y", "nodejs-lts"],
                    capture_output=True, text=True, timeout=300,
                )
                if r.returncode == 0:
                    if verbose: print("  Node.js installed.")
                else:
                    if verbose:
                        print("  Node.js install FAILED.")
                        err = r.stderr.strip().split("\n")[-1] if r.stderr else ""
                        if err: print(f"    {err}")
                    return False
            except Exception as e:
                if verbose: print(f"  Node.js install ERROR: {e}")
                return False
        else:
            if verbose:
                print("  [SKIP] Node.js not found. Install node first.")
            return False

    # ── Step 2: Claude Code CLI ──
    if verbose:
        print(f"  Installing {_CLAUDE_CODE_PKG}...", flush=True)
    try:
        r = subprocess.run(
            ["npm", "install", "-g", _CLAUDE_CODE_PKG],
            capture_output=True, text=True, timeout=300,
        )
        if r.returncode == 0:
            if verbose: print("  Claude Code CLI installed.")
        else:
            if verbose:
                print("  Claude Code CLI FAILED.")
                err = r.stderr.strip().split("\n")[-1] if r.stderr else ""
                if err: print(f"    {err}")
            return False
    except Exception as e:
        if verbose: print(f"  Claude Code CLI ERROR: {e}")
        return False

    # ── Step 3: Disable auto-update ──
    claude_dir = os.path.expanduser("~/.claude")
    config_path = os.path.join(claude_dir, "config.json")
    if not os.path.exists(config_path):
        try:
            os.makedirs(claude_dir, exist_ok=True)
            with open(config_path, "w") as f:
                f.write('{"autoUpdater":{"disabled":true}}\n')
            if verbose: print("  Auto-update disabled.")
        except Exception:
            pass

    # ── Step 4: ws package ──
    if verbose:
        print("  Installing ws (npm)...", end=" ", flush=True)
    try:
        r = subprocess.run(
            ["npm", "install", "ws"],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.expanduser("~"),
        )
        if r.returncode == 0:
            if verbose: print("OK")
        else:
            if verbose: print("FAILED (bridge may not work)")
    except Exception:
        if verbose: print("FAILED")

    # ── Step 5: Copy bridge.js ──
    _copy_bridge(verbose=verbose)

    # ── Step 6: Claude authentication ──
    _authenticate_claude(verbose=verbose)

    if verbose:
        print()
        print("  Claude Code setup complete.")
        print("  Start bridge: node ~/bridge.js")

    return True


def _authenticate_claude(verbose: bool = True):
    """Launch claude CLI interactively for login/auth."""
    # Find cli.js path
    cli_path = _find_claude_cli_js()
    if not cli_path:
        if verbose:
            print("  [SKIP] Claude CLI js not found for auth.")
        return

    # Check if already authenticated (quick test)
    try:
        r = subprocess.run(
            ["node", cli_path, "-p", "Return only OK",
             "--output-format", "stream-json", "--verbose"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0 and "OK" in r.stdout:
            if verbose:
                print("  Claude auth: already authenticated.")
            return
    except Exception:
        pass

    # Need login — run interactively
    if verbose:
        print()
        print("  Claude login required.")
        print("  A browser will open for authentication.")
        print("  After login, type /exit to return.")
        print()

    try:
        answer = input("  Open Claude login now? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if answer not in ("y", "yes"):
        if verbose:
            print("  Skipped. Login later: node " + cli_path)
        return

    # Run claude CLI interactively (stdin/stdout/stderr pass-through)
    try:
        subprocess.run(
            ["node", cli_path],
            timeout=300,
        )
        if verbose:
            print("  Auth complete.")
    except subprocess.TimeoutExpired:
        if verbose:
            print("  Auth timed out. Try again: node " + cli_path)
    except Exception as e:
        if verbose:
            print(f"  Auth error: {e}")


def _find_claude_cli_js() -> str:
    """Find claude-code cli.js path."""
    try:
        root = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        import os as _os
        p = _os.path.join(root, "@anthropic-ai", "claude-code", "cli.js")
        if _os.path.exists(p):
            return p
    except Exception:
        pass
    return None


def _copy_bridge(verbose: bool = True):
    """Copy bridge.js from usekit package to ~/bridge.js."""
    home = os.path.expanduser("~")
    dst = os.path.join(home, "bridge.js")

    if os.path.exists(dst):
        if verbose: print("  bridge.js already exists in ~/")
        return

    # Find bridge.js in usekit package
    try:
        import usekit
        pkg_dir = os.path.dirname(os.path.abspath(usekit.__file__))
        # Check common locations
        for rel in ["tools/bridge/bridge.js", "bridge.js"]:
            src = os.path.join(pkg_dir, rel)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                if verbose: print(f"  Copied bridge.js → ~/bridge.js")
                return
    except Exception:
        pass

    if verbose:
        print("  bridge.js not found in package. Copy manually to ~/bridge.js")


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
