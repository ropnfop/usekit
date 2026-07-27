# Behavioral CHECK for ue.dhsl — logic correctness (run: python3 _check_dhsl.py)
#
# LOGIC proof (runs the primitives). `uk verify` is mechanical (grep) and
# cannot run this. Run both.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dhsl as D  # noqa: E402

X = "E2R2S1D1F2"

CHECKS = [
    # shared_depth — strict hierarchy
    ("shared_depth identical=5",      D.shared_depth(X, X) == 5),
    ("shared_depth diverge@D=3",      D.shared_depth(X, "E2R2S1D9F9") == 3),
    ("shared_depth diverge@E=0",      D.shared_depth(X, "E9R2S1D1F2") == 0),
    # diff — graded, earlier axis heavier
    ("diff identical=0",              D.diff(X, X) == 0),
    ("diff E by1 =16",                D.diff("E0R0S0D0F0", "E1R0S0D0F0") == 16),
    ("diff R by1 =8",                 D.diff("E0R0S0D0F0", "E0R1S0D0F0") == 8),
    ("diff F by1 =1",                 D.diff("E0R0S0D0F0", "E0R0S0D0F1") == 1),
    ("diff neg-paren E by1 =16",      D.diff("E0R0S0D0F0", "E(1)R0S0D0F0") == 16),
    ("shared_depth neg-paren@D=3",    D.shared_depth("E2R(2)S1D1F2", "E2R(2)S1D9F9") == 3),
    ("diff B-mode equal weights",     D.diff("E0R0S0D0F0", "E1R0S0D0F1", weights=(1, 1, 1, 1, 1)) == 2),
    # diff_norm — single 0..1 normalized ruler (stall eps / reward / leak share it)
    ("diff_norm identical=0",         D.diff_norm(X, X) == 0.0),
    ("diff_norm small in (0,1)",      0 < D.diff_norm("E0R0S0D0F0", "E0R0S0D2F0", weights=(8, 6, 6, 10, 4)) < 1),
    ("diff_norm larger span->smaller", D.diff_norm("E0R0S0D0F0", "E0R0S0D1F0", span=4) > D.diff_norm("E0R0S0D0F0", "E0R0S0D1F0", span=8)),
    # nearest
    ("nearest picks closest",         D.nearest(X, ["E9R0S0D0F0", "E2R2S1D1F0", "E0R0S0D0F0"]) == "E2R2S1D1F0"),
    ("nearest empty -> None",         D.nearest(X, []) is None),
    # flow gate
    ("bump raises",                   D.bump(2.0, 1.0) == 3.0),
    ("decay idle1 rate.5 =1.5",       D.decay(3.0, 1, 0.5) == 1.5),
    ("decay idle0 = same",            D.decay(3.0, 0) == 3.0),
    ("reorder freq first",            D.reorder([("a", 1.0), ("b", 3.0), ("c", 2.0)]) == ["b", "c", "a"]),
    ("reorder stable on tie",         D.reorder([("a", 1.0), ("b", 1.0)]) == ["a", "b"]),
]

if __name__ == "__main__":
    ok = all(r for _, r in CHECKS)
    for n, r in CHECKS:
        print(("OK  " if r else "FAIL") + "  " + n)
    print("ALL PASS" if ok else "FAILED")
    sys.exit(0 if ok else 1)
