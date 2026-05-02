# Path: usekit.classes.data.base.load.sub.dbl_has_sub.py
# -----------------------------------------------------------------------------------------------
#  DATA EXISTS OPERATION ONLY (Light-weight sub module)
#  Purpose: Check file existence
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Union

from usekit.classes.data.base.load.sub.dbl_common_sub import _ensure_path_obj

__all__ = ["proc_has_data"]


def proc_has_data(
    fmt: str,
    path: Union[str, Path],
    **kwargs
) -> bool:
    """
    Check if file has.
    """
    return _ensure_path_obj(path).is_file()


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------