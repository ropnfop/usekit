# Path: usekit.classes.support.base.init.emo.hslva
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# — memory is emotion —
#
# ue.hslva — pure HSL -> HSLVA code utility (emotion/texture channel).
# Ported from SRSNOTE hslva_code.py (STEP B of the EMO build plan).
#
# PURE transform only: no DB, no timestamp, no previous-state, no I/O.
#   (dHSL / flow gating belongs to ue.dhsl; feedback assembly to ue.roop.)
#
# Exposed as `ue.hslva` via EmoHandler in sbi_emo.py.
# -----------------------------------------------------------------------------------------------

from typing import Tuple

_HUE_RING = "ROYGCBVM"  # 8 sectors, 45 degrees each

# upper bound, letter — first bound a value is <= wins; above .95 saturates to J
_LEVELS = (
    (0.15, "A"), (0.25, "B"), (0.35, "C"), (0.45, "D"), (0.55, "E"),
    (0.65, "F"), (0.75, "G"), (0.85, "H"), (0.95, "I"),
)

# Hue meaning carries polarity via letter case (neg=upper, pos=lower).
_MEANING_NEG = {"R": "위기", "O": "긴장", "Y": "경계", "G": "의지",
                "C": "집중", "B": "이완", "V": "피로", "M": "정체"}
_MEANING_POS = {"r": "위기", "o": "긴장", "y": "경계", "g": "안정",
                "c": "집중", "b": "이완", "v": "몰입", "m": "정체"}


def hue_sector(h: int) -> str:
    """Map a hue in degrees to one of 8 emotion-ring letters (45-deg sectors)."""
    return _HUE_RING[int(h % 360 // 45)]


def encode_level(v: float) -> str:
    """Quantize a 0..1(+) value to A..J. Values above .95 saturate to J
    (V can reach ~1.25 by design, so the upper bound must be absorbed)."""
    for thr, ch in _LEVELS:
        if v <= thr:
            return ch
    return "J"


def derive(s: float, l: float) -> Tuple[float, float]:
    """Derive V (action force) and A (mean activation) from S and L.
    V formula kept as-is from the original (max ~1.25); DO NOT change here.
    A future fix should be a separate v2/option, not an edit to this."""
    v = (s * l) / 8 * 10
    a = (s + l) / 2
    return (v, a)


def to_code(h: int, s: float, l: float, polarity: bool = True) -> str:
    """Build the 5-letter HSLVA code (H S L V A).
    polarity: neg (UPPER) when l < 0.5 and s >= 0.6, else pos (lower)."""
    v, a = derive(s, l)
    code = (
        hue_sector(h)
        + encode_level(s)
        + encode_level(l)
        + encode_level(v)
        + encode_level(a)
    )
    if polarity:
        neg = (l < 0.5 and s >= 0.6)
        code = code.upper() if neg else code.lower()
    return code


def classify(code: str) -> str:
    """Read hue letters (every 5th char) into an emotion trajectory.
    Case carries polarity, e.g. G의지 / g안정, V피로 / v몰입."""
    out = []
    for c in code[::5]:
        out.append(_MEANING_NEG.get(c) or _MEANING_POS.get(c) or c)
    return " → ".join(out)
