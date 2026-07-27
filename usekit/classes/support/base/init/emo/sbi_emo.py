# Path: usekit.classes.support.base.init.emo.sbi_emo
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# — memory is emotion —
#
# Emotion Support Handler — ue
#
# The emotion/knowledge-decomposition subsystem. Pure-utility namespace,
# sibling to uu/ut/uw/ud/us/uk/ua. Each member is a pure transform module
# (data in -> data out): no DB, no timestamp, no previous-state, no auto-
# dispatch. Assembly/feedback belongs to the app layer (SRSNOTE), so usekit's
# generic build() is never contaminated by emotion logic.
#
# Usage:
#   from usekit import ue
#   ue.hslva.to_code(120, 0.6, 0.65)   # -> "yffef"
#
# Design notes:
#   - Same handler+singleton shape as sbi_util.uu, lazy-wrapped in use_support.
#   - Pure modules import nothing from usekit -> no import cycles.
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

# Pure transform modules (no side effects). Attached as-is; functions are
# module-level, so no instance state is needed.
from usekit.classes.support.base.init.emo import hslva as _hslva
from usekit.classes.support.base.init.emo import ersdf as _ersdf
from usekit.classes.support.base.init.emo import dhsl as _dhsl


class EmoHandler:
    """ue — emotion/knowledge utilities. Exposes pure coordinate transforms.
    Current: ue.hslva (HSL<->HSLVA emotion code), ue.ersdf (knowledge address
    codec), ue.dhsl (coordinate diff + flow gate). Planned: ue.meta (pure, STEP
    E) and ue.roop (assembly, STEP F)."""

    def __init__(self):
        # HSL -> 5-letter HSLVA code (EMO STEP B). Pure module attached directly.
        self.hslva = _hslva
        # 5-level ERSDF knowledge-address codec (EMO STEP C). Pure module.
        self.ersdf = _ersdf
        # Coordinate diff + usage flow gate (EMO STEP D). Pure module.
        self.dhsl = _dhsl

    def __repr__(self):
        return "<EmoHandler ue [hslva | ersdf | dhsl]>"


# module-level singleton (lazy-wrapped in use_support)
ue = EmoHandler()


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
