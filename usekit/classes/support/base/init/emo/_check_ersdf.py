# Behavioral CHECK for ue.ersdf — PAREN-NEGATIVE canonical scheme (run: python3 _check_ersdf.py)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ersdf as E  # noqa: E402

def _raises(fn):
    try: fn(); return False
    except Exception: return True

CHECKS = [
    # codec — canonical: bare-digit positives, parenthesized negatives, no +/-
    ("to_code mixed",             E.to_code(2, -2, 1, 1, 2) == "E2R(2)S1D1F2"),
    ("to_code all neg",           E.to_code(-1, -7, -4, -3, -8) == "E(1)R(7)S(4)D(3)F(8)"),
    ("to_code zero -> 0",         E.to_code(0, 0, 0, 0, 0) == "E0R0S0D0F0"),
    ("parse roundtrip signed",    E.parse("E1R(2)S7D4F(8)") == (1, -2, 7, 4, -8)),
    ("clamp 12/-12/99 -> 9/-9/9", E.to_code(12, -12, 3, 5, 99) == "E9R(9)S3D5F9"),
    ("is_valid canonical ok",     E.is_valid("E2R(2)S1D1F2") is True),
    ("is_valid all-pos ok",       E.is_valid("E1R7S4D3F8") is True),
    ("is_valid old +/- -> False", E.is_valid("E+2R-2S+1D+1F+2") is False),
    ("is_valid bare minus -> F",  E.is_valid("E2R-2S1D1F2") is False),
    ("is_valid wrong letter",     E.is_valid("X2R(2)S1D1F2") is False),
    ("is_valid empty",            E.is_valid("") is False),
    ("parse bad raises",          _raises(lambda: E.parse("nope"))),
    # prefix — sliced by AXIS now (variable width)
    ("prefix d1 -> E2",           E.prefix("E2R(2)S1D1F2", 1) == "E2"),
    ("prefix d2 -> E2R(2)",       E.prefix("E2R(2)S1D1F2", 2) == "E2R(2)"),
    ("prefix d3 -> E2R(2)S1",     E.prefix("E2R(2)S1D1F2", 3) == "E2R(2)S1"),
    ("prefix d0 -> ''",           E.prefix("E2R(2)S1D1F2", 0) == ""),
    ("prefix overflow -> full",   E.prefix("E2R(2)S1D1F2", 9) == "E2R(2)S1D1F2"),
    # meaning — sign = valence, magnitude = activation
    ("polarity 0 -> NA",          E.polarity(0) == "NA"),
    ("polarity +5 -> POS",        E.polarity(5) == "POS"),
    ("polarity -2 -> NEG",        E.polarity(-2) == "NEG"),
    ("label rel +9 긍정",          E.label("rel", 9) == "강한 긍정관계"),
    ("label rel -9 갈등",          E.label("rel", -9) == "강한 갈등관계"),
    ("label env 0 중립",           E.label("env", 0) == "판단불가/중립"),
    ("label feel -8 부정감정",      E.label("feel", -8) == "강한 부정감정"),
    ("describe signed cell",      E.describe("E2R(2)S1D1F(8)")["feel"] == {"value": -8, "label": "강한 부정감정", "polarity": "NEG"}),
    ("describe bad -> {}",        E.describe("nope") == {}),
]

if __name__ == "__main__":
    ok = all(r for _, r in CHECKS)
    for n, r in CHECKS: print(("OK  " if r else "FAIL") + "  " + n)
    print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
