# Path: usekit.classes.data.base.load.sub.dbl_delete_sub.py
# -----------------------------------------------------------------------------------------------
#  DATA DELETE OPERATION ONLY (Light-weight sub module)
#  Purpose: Delete data file safely
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Union

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.data.base.load.sub.dbl_common_sub import _ensure_path_obj

__all__ = ["proc_delete_data"]


@log_and_raise
def proc_delete_data(
    fmt: str,
    path: Union[str, Path],
    *,
    missing_ok: bool = True,
    **kwargs
) -> bool:
    """
    Delete data file.

    Returns:
        True if file deleted, False if missing (and missing_ok=True)
    """
    path_obj = _ensure_path_obj(path)

    if not path_obj.exists():
        if missing_ok:
            return False
        raise FileNotFoundError(f"File not found: {path_obj}")

    if not path_obj.is_file():
        raise IsADirectoryError(f"Not a file: {path_obj}")

    path_obj.unlink()
    return True


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------