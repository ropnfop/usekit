# MIT License. See project root LICENSE file.
# Path: usekit/__init__.py
# ----------------------------------------------------------------------------------------------- 
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- 

# Suppress banner when invoked via CLI entry point
import os as _os, sys as _sys
if any("usekit.cli" in arg for arg in _sys.argv[:1]) or \
   _sys.argv and _sys.argv[0].endswith(("uk", "usekit")):
    _os.environ.setdefault("USEKIT_QUIET", "1")

# Import all from usemain
from .classes.core.env.loader_env import load_env
load_env()
from .usemain import *

# Version info
__version__ = "0.2.0"
__author__ = "THE Little Prince"

# ----------------------------------------------------------------------------------------------- 
#  [ withropnfop@gmail.com ]  
# -----------------------------------------------------------------------------------------------