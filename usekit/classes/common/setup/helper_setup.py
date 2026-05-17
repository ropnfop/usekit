# Path: usekit.classes.common.setup.helper_setup
# -----------------------------------------------------------------------------------------------
# Main orchestrator for use.setup() — interactive workspace initializer
# -----------------------------------------------------------------------------------------------

from typing import Optional


def setup(verbose: bool = True, interactive: bool = True) -> bool:
    """
    Full interactive setup wizard for USEKIT workspace.
    
    Flow:
        1. Detect system environment
        2. Check core dependencies
        3. Resolve project name/path
        4. Termux storage setup (Termux only)
        5. Editor behavior options
        6. Create directories + sys_project.yaml
        7. Run use.check()
        8. Optional editor launch
    
    Args:
        verbose: Show detailed output
        interactive: Allow user input prompts
    
    Returns:
        bool: True if setup completed successfully
    
    Examples:
        >>> from usekit import use
        >>> use.setup()
    """
    from usekit.classes.common.setup.helper_setup_env import (
        detect_environment,
        check_dependencies,
    )
    from usekit.classes.common.setup.helper_setup_project import resolve_project
    from usekit.classes.common.setup.helper_setup_config import (
        ask_editor_options,
        create_project_structure,
        build_sys_project_data,
        write_sys_project,
        copy_source_configs,
    )

    # ── Step 1: Environment ──
    env = detect_environment(verbose=verbose)

    # ── Step 2: Dependencies ──
    core, optional = check_dependencies(verbose=verbose)
    missing_core = [n for n, ok in core.items() if not ok]
    if missing_core:
        print()
        print("[SETUP] Core dependencies missing. Please install them first.")
        return False

    # ── Step 3: Project name/path ──
    result = resolve_project(verbose=verbose)
    if result is None:
        return False
    project_name, project_path = result

    # ── Step 4: Termux storage (Termux only) ──
    if env["platform"] == "termux":
        print()
        try:
            answer = input("Setup Termux storage? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Skipped Termux storage.")
            answer = "n"

        if answer in ("y", "yes"):
            try:
                from usekit.classes.common.init.helper_termux_storage import termux
                print("Running use.termux()...")
                termux(verbose=verbose, interactive=False)
                print("Storage OK.")
            except ImportError:
                print("[WARN] Termux storage helper not available.")
            except Exception as e:
                print(f"[WARN] Termux storage setup failed: {e}")

    # ── Step 5: Editor options ──
    editor_config = ask_editor_options(verbose=verbose)

    # ── Step 6: Create structure + save config ──
    if not create_project_structure(project_path, verbose=verbose):
        return False

    project_data = build_sys_project_data(project_name, editor_config)

    if not write_sys_project(project_path, project_data, verbose=verbose):
        return False

    if not copy_source_configs(project_path, project_name, verbose=verbose):
        if verbose:
            print("[WARN] Some config files could not be copied.")

    # Clear caches after path changes
    _clear_caches()

    # ── Step 6b: Editor autostart (Termux only) ──
    if env["platform"] == "termux":
        try:
            from usekit.classes.common.init.helper_termux_storage import _register_editor_autostart
            _register_editor_autostart(
                enable=editor_config.get("autostart", False),
                verbose=verbose,
            )
        except ImportError:
            pass

    # ── Step 7: Validation ──
    print()
    try:
        from usekit.classes.wrap.base.use_interface import check
        check(verbose=verbose)
    except ImportError:
        if verbose:
            print("[INFO] Skipped validation (check module not available).")

    # ── Step 8: Optional editor launch ──
    if interactive:
        print()
        try:
            answer = input("Start usekit editor? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer in ("y", "yes"):
            try:
                from usekit.classes.wrap.base.use_interface import editor
                editor()
            except ImportError:
                print("[WARN] Editor module not available.")
            except Exception as e:
                print(f"[WARN] Editor launch failed: {e}")
        else:
            if verbose:
                print("Skipped editor launch.")

    # ── Done ──
    if verbose:
        print()
        print("=" * 60)
        print("[USEKIT] Setup complete!")
        print("=" * 60)
        print()
        print("Quick start:")
        print("  from usekit import use, u")
        print("  use.check()        # verify environment")
        print("  use.editor()       # start editor")
        print()

    return True


def _clear_caches():
    """Clear all relevant caches after setup changes."""
    try:
        from usekit.classes.common.utils.helper_const import (
            clear_sys_const_cache,
            clear_sys_project_cache,
        )
        clear_sys_const_cache()
        clear_sys_project_cache()
    except ImportError:
        pass

    try:
        from usekit.classes.common.utils.helper_env import clear_cache
        clear_cache()
    except ImportError:
        pass

    try:
        from usekit.classes.common.utils.helper_data_cache import clear_all_cache
        clear_all_cache()
    except ImportError:
        pass


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
