# Behavioral CHECK for uu.hslva — logic correctness (run with: python3 _check_hslva.py)
#
# This is the LOGIC proof: it actually runs the functions and compares output.
# `uk verify` is mechanical (grep/node) and CANNOT run this; it only confirms
# placement/wiring. Run both: python3 here for logic, `uk verify` for structure.
#
# float values use approx compare (derive returns raw float, quantized later).

import os
import sys

# Make `import hslva` work regardless of CWD (this file sits next to hslva.py).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hslva as H  # noqa: E402


def approx(a, b, eps=1e-9):
    return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps


CHECKS = [
    ("hue_sector(120)=Y",             H.hue_sector(120) == "Y"),
    ("encode_level(0.6)=F",           H.encode_level(0.6) == "F"),
    ("encode_level(0.65)=F",          H.encode_level(0.65) == "F"),
    ("encode_level(0.5)=E",           H.encode_level(0.5) == "E"),
    ("encode_level(1.25)=J",          H.encode_level(1.25) == "J"),   # upper-bound absorb
    ("derive(0.6,0.65)~(.4875,.625)", approx(H.derive(0.6, 0.65), (0.4875, 0.625))),
    ("to_code(120,0.6,0.65)=yffef",   H.to_code(120, 0.6, 0.65) == "yffef"),   # pos
    ("to_code(120,0.7,0.4)=YGDCE",    H.to_code(120, 0.7, 0.4) == "YGDCE"),    # neg/upper
]

if __name__ == "__main__":
    ok = all(r for _, r in CHECKS)
    for n, r in CHECKS:
        print(("OK  " if r else "FAIL") + "  " + n)
    print("ALL PASS" if ok else "FAILED")
    sys.exit(0 if ok else 1)
