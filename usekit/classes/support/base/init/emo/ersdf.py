# Path: usekit.classes.support.base.init.emo.ersdf
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# — memory is emotion —
#
# ue.ersdf — pure knowledge-address codec (STEP C of the EMO build plan).
#
# The address is a 5-level signed coordinate, one SIGNED value (-9..+9) per axis,
# in fixed order E R S D F. Each axis carries BOTH magnitude and valence:
#   magnitude (|v|, 1..9) = activation degree (얼마나 활성/관여)
#   sign                  = valence: + 긍정,  - 부정
#   0                     = 판단불가 / 중립 (info-insufficient or neutral)
# (어린왕자 2026-06-09: valence pulled INTO the coordinate as the sign, so the
#  charge is conveyed first-class instead of relegated to a binary color flag.)
#
# Code string format — axis-letter + value, value written canonically as:
#   positive / zero : bare digit          E2  (env +2),  S0 (self 0)
#   negative        : digit in parens     R(2) (rel -2)
#   NO '+' sign, NO '-' sign — negatives are represented ONLY by parentheses.
#   e.g.  'E1R7S4D3F8'  (all positive),  'E2R(2)S4D(4)F6'  (R,? note R+2 here)
#         'E(2)R2S4D(4)F6'  =  env -2, rel +2, self +4, drive -4, feel +6
# (어린왕자 2026-06-09: parens chosen over a leading '-' so a negative reads as a
#  single bracketed unit, and so ersdf never reuses the hyphen that HSLVA period
#  codes use as a separator (G-O-O-B). Both notations stay visually distinct.
#  NOTE for the .km layer: '()' also means composition in the .km grammar, so an
#  ersdf code must be carried there as an atomic / quoted value, never as a bare
#  token, or the .km parser may mistake it for a composition expression.)
#
#   E = environment (환경)        [confirmed]
#   R = relationship (관계) / S = self (자아) / D = drive (의지) / F = feel (감정)
#
# PURE codec + readable gloss only — pack / unpack / validate / prefix + labels.
# NO storage, NO usage logic.
#   - distance / coordinate-diff + the usage flow-gate belong to ue.dhsl (STEP D);
#     diff/shared_depth read parse() so they work on signed values unchanged.
#   - the tree storage + leaf-word indexing belong to the user DB (data layer).
#   - the LLM seed-estimate prompt belongs to assembly (STEP G).
#
# Exposed as `ue.ersdf` via EmoHandler in sbi_emo.py.
# -----------------------------------------------------------------------------------------------

import re
from typing import Tuple

_AXES = "ERSDF"                       # fixed order, 5 levels (E coarsest .. F finest)

# One axis value: a parenthesized digit '(d)' for negatives, or a bare digit 'd'
# for positive / zero. No '+' or '-' ever appears in a canonical code.
_VAL = r"(\(\d\)|\d)"
_RX = re.compile("^E" + _VAL + "R" + _VAL + "S" + _VAL + "D" + _VAL + "F" + _VAL + "$")

# One 'letter + value' chunk, used to slice a code by AXIS (codes are now
# variable-width: 'E2' is 2 chars, 'E(2)' is 4), so prefix can no longer cut by
# a fixed char count.
_AXIS_TOKEN = re.compile(r"[ERSDF](?:\(\d\)|\d)")


def _clamp(v: int) -> int:
    """Coerce an axis value into the signed range -9..+9.
    Seed estimates are rough, so out-of-range input is clamped, not rejected."""
    v = int(v)
    return -9 if v < -9 else 9 if v > 9 else v


def _fmt(v: int) -> str:
    """One axis value -> canonical token. Positive/zero is a bare digit; a
    negative is its magnitude in parentheses. e.g. 5 -> '5', 0 -> '0', -7 -> '(7)'."""
    return "(" + str(-v) + ")" if v < 0 else str(v)


def _unfmt(tok: str) -> int:
    """One captured axis value ('5' or '(7)') -> signed int."""
    return -int(tok[1:-1]) if tok.startswith("(") else int(tok)


def to_code(e: int, r: int, s: int, d: int, f: int) -> str:
    """Pack five SIGNED axis values (-9..+9 each) into a canonical code, e.g.
    to_code(2, -2, 1, 1, 2) -> 'E2R(2)S1D1F2'. Values outside range are clamped.
    Positive/zero are bare digits; negatives are parenthesized."""
    vals = (_clamp(e), _clamp(r), _clamp(s), _clamp(d), _clamp(f))
    return "".join(a + _fmt(v) for a, v in zip(_AXES, vals))


def parse(code: str) -> Tuple[int, int, int, int, int]:
    """Unpack a canonical code back into signed (e, r, s, d, f). Raises ValueError
    on a malformed code (use is_valid first if input is untrusted).
    e.g. parse('E1R(2)S7D4F(8)') -> (1, -2, 7, 4, -8)."""
    m = _RX.match(code or "")
    if not m:
        raise ValueError(f"bad ersdf code: {code!r}")
    return tuple(_unfmt(g) for g in m.groups())  # type: ignore[return-value]


def is_valid(code: str) -> bool:
    """True iff code is a well-formed canonical address (bare-digit positives,
    parenthesized negatives, no +/- signs). Old +/- codes return False."""
    return bool(_RX.match(code or ""))


def prefix(code: str, depth: int) -> str:
    """Return the ancestor address at the given depth (1=E .. 5=full), sliced by
    AXIS (not by char, since codes are variable-width now).
    e.g. prefix('E2R(2)S1D1F2', 1) -> 'E2', depth 2 -> 'E2R(2)'. depth clamped 0..5."""
    depth = 0 if depth < 0 else 5 if depth > 5 else int(depth)
    return "".join(_AXIS_TOKEN.findall(code or "")[:depth])


# -----------------------------------------------------------------------------------------------
# Meaning layer — SIGNED ACTIVATION (어린왕자 2026-06-09).
# Codec above stays format-only; these turn a bare code into something readable.
# Every axis reads the same way: |value| = how active (1 약 .. 9 강), sign = valence
# (+ 긍정 / - 부정), 0 = 판단불가/중립. So a single signed number carries both
# "얼마나 셌나" and "긍이냐 부냐" — the charge the color used to flag binarily.
# -----------------------------------------------------------------------------------------------

# Human axis names, aligned with the frontend KEYS order (E R S D F).
AXES = ("env", "rel", "self", "drive", "feel")

# Per-axis valence poles: (positive pole, negative pole).
POLES = {
    "env":   ("긍정환경", "부정환경"),
    "rel":   ("긍정관계", "갈등관계"),
    "self":  ("긍정자기인식", "부정자기인식"),
    "drive": ("추진의지", "회피저항"),
    "feel":  ("긍정감정", "부정감정"),
}


def _mag_word(mag: int) -> str:
    """Activation-magnitude gloss for |value| (1..9)."""
    return "약한" if mag <= 3 else "보통" if mag <= 6 else "강한"


def polarity(value: int) -> str:
    """Valence of a signed axis value.
    > 0 -> 'POS' (긍정),  < 0 -> 'NEG' (부정),  0 -> 'NA' (판단불가/중립)."""
    if value == 0:
        return "NA"
    return "POS" if value > 0 else "NEG"


def label(axis: str, value: int) -> str:
    """Human label for a signed axis value: magnitude word + valence pole.
    e.g. rel +9 -> '강한 긍정관계', rel -8 -> '강한 갈등관계', feel 0 -> '판단불가/중립'."""
    if value == 0:
        return "판단불가/중립"
    poles = POLES.get(axis)
    if not poles:
        return str(value)
    pole = poles[0] if value > 0 else poles[1]
    return f"{_mag_word(abs(value))} {pole}"


def describe(code: str) -> dict:
    """Expand a code into per-axis {value, label, polarity} — turns a bare
    'E2R(2)S1D1F(8)' into something feelable. Returns {} on a malformed code."""
    if not is_valid(code):
        return {}
    vals = parse(code)
    return {
        ax: {"value": v, "label": label(ax, v), "polarity": polarity(v)}
        for ax, v in zip(AXES, vals)
    }
