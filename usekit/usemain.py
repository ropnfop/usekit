# MIT License. See project root LICENSE file.
# Path: usekit.usemain.py
# ----------------------------------------------------------------------------------------------- 
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- 

# [USEKIT TICKER LOG : True/False]
import sys
from usekit.classes.common.utils.helper_timer import _tick, _clear
_clear()
_tick("USEKIT ON")

# [DEBUG MODE LOG : True/False]
from usekit.classes.common.errors.helper_setupdebug import print_loader_debug
print_loader_debug()
_tick("USEKIT import setupdebug")

# [MAIN INTERFACES]
from usekit.classes.wrap.base.use_base import use, u
_tick("USEKIT use loaded")

# [SAFE LOAD LOG: True/False]
from usekit.classes.wrap.safe.use_safe import safe, s
_tick("USEKIT safe loaded")

# [OPTIONAL: PRELOAD SAFE IN BACKGROUND]
# Colab + Drive 없음은 skip (휘발성 환경, 임포트 속도 우선)
from usekit.classes.wrap.base.use_base import _should_preload
if _should_preload():
    safe.preload()
_tick("USEKIT safe preload started")

# [SUPPORT UTILITIES: Time & Watch & Database]
from usekit.classes.wrap.sub.use_support import ut, uw, ud
_tick("USEKIT support loaded")

# [REFIXING EXTENSIONS]
# Rebinding and reloading optional extension modules for dynamic usekit augmentation
# from usekit.classes.class_ext import ext 
# from usekit.classes.classrefs.refs_use_ext  import utt, uww, uai, udd, u, w, t
# from usekit.classes.classrefs.refs_aliases import uf, e, ef
# from usekit.classes.classrefs.refs_usesafe import usf, stt, sai
# from usekit.classes.classrefs.refs_extsafe import esf

# More learn use.help()

# [EXPORT DEFINITIONS]
__all__ = [    
    "use", "u", "safe", "s", "ut", "uw", "ud"
    # "utt", "uww", "udd", "uai", "ext",
    # "usf", "esf", "u", "uf", "e", "ef", "w", "t"
]

# [LOADER STATUS]
_tick("USEKIT LOAD")
import os as _os
if not _os.environ.get("USEKIT_QUIET"):
    print("[Memory is emotion]")
del _os

# ----------------------------------------------------------------------------------------------- 
#  [ withropnfop@gmail.com ]  
# ----------------------------------------------------------------------------------------------- 