# Path: usekit.classes.support.base.init.emo.dhsl
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# — memory is emotion —
#
# ue.dhsl — pure coordinate diff + flow gate (STEP D of the EMO build plan).
#
# This is the "feel it" layer for the self-sorting behaviour: things used often
# rise, things left idle drift back, and order emerges from usage. Nothing here
# is final policy — these are small, tunable primitives to play with on-device,
# then lock in once the feel is right.
#
# Two lenses on "distance":
#   shared_depth(a, b) -> 0..5   strict hierarchy: how many leading axes match
#                                ("같은 E2면 한 동네"; magnitude ignored)
#   diff(a, b)        -> int     graded: earlier axis weighs more (16·8·4·2·1
#                                default, tunable). magnitude counts.
# Flow gate (usage -> position), score is SEPARATE from the address:
#   bump / decay / reorder       a use bumps a score up, idle decays it, reorder
#                                surfaces the frequent ones. The ersdf address
#                                stays the stable filing key; the score carries
#                                the dynamic rank.
#
# PURE only — no DB, no timestamp, no I/O. Count/recency STORAGE is the user DB.
# Whether the score should feed back into the address (mutating the coordinate)
# is an assembly/policy question for later (STEP F) — not decided here.
#
# Exposed as `ue.dhsl` via EmoHandler in sbi_emo.py.
# -----------------------------------------------------------------------------------------------

from typing import List, Optional, Tuple

# Reuse the address codec as the substrate (pure -> pure, no cycle).
# Absolute import in production (loaded as part of usekit); sibling fallback so
# the standalone _check_dhsl.py can run without the full package on the path.
try:
    from usekit.classes.support.base.init.emo import ersdf as _ersdf
except ImportError:  # standalone (e.g. python3 _check_dhsl.py next to this file)
    import ersdf as _ersdf  # type: ignore

# Default graded weights, coarse axis (E) heaviest .. fine axis (F) lightest.
# Tune freely: pass weights=(1, 1, 1, 1, 1) for the "all axes equal" feel (B).
_DEFAULT_WEIGHTS = (16, 8, 4, 2, 1)


def shared_depth(a: str, b: str) -> int:
    """Strict-hierarchy proximity: count of leading axes that match before the
    first divergence (0..5). Same E -> >=1, same E&R -> >=2, identical -> 5.
    This is the tree '한 동네' measure; it ignores how far apart values are."""
    va, vb = _ersdf.parse(a), _ersdf.parse(b)
    n = 0
    for x, y in zip(va, vb):
        if x != y:
            break
        n += 1
    return n


def diff(a: str, b: str, weights: Tuple[int, ...] = _DEFAULT_WEIGHTS) -> int:
    """Graded distance: weighted sum of per-axis absolute differences. Earlier
    axes weigh more by default, so divergence near the root costs more than near
    the leaf — but magnitude still counts (unlike shared_depth)."""
    va, vb = _ersdf.parse(a), _ersdf.parse(b)
    return sum(w * abs(x - y) for w, x, y in zip(weights, va, vb))


# The representative per-axis move that should read as "fully moved" (1.0) in the
# normalized scale below. The THEORETICAL max is 18 (-9..+9), but real per-turn
# moves are far smaller, so dividing by the theoretical max buries every velocity
# near 0. A representative span keeps 0..1 meaningful. TUNABLE — lock in on-device
# once the velocity distribution is known.
_NORM_SPAN = 4


def diff_norm(a: str, b: str, weights: Tuple[int, ...] = _DEFAULT_WEIGHTS,
              span: float = _NORM_SPAN) -> float:
    """Normalized graded distance in ~0..1: diff(a, b, weights) / (sum(weights) *
    span). This is the ONE place coordinate speed/distance is put on a 0..1 scale,
    so every threshold built on it — freeze stall (eps), reward, leak — shares the
    same ruler. Returns 0.0 on a non-positive divisor; may exceed 1.0 for very
    large moves (callers compare against a low eps, so the upper bound is moot)."""
    denom = sum(weights) * span
    return diff(a, b, weights) / denom if denom > 0 else 0.0


def nearest(target: str, candidates: List[str]) -> Optional[str]:
    """Return the candidate closest to target by diff (retrieval feel).
    None if candidates is empty. Ties resolve to the first seen."""
    best, best_d = None, None
    for c in candidates:
        d = diff(target, c)
        if best_d is None or d < best_d:
            best, best_d = c, d
    return best


def bump(score: float, amount: float = 1.0) -> float:
    """A use raises the score (rises toward the top). Pure: returns new score."""
    return score + amount


def decay(score: float, idle: int, rate: float = 0.5) -> float:
    """Idle pulls the score down, multiplicatively: score * rate**idle.
    rate in (0,1); idle is the number of idle steps. Never goes negative."""
    idle = max(0, int(idle))
    return score * (rate ** idle)


def reorder(scored: List[Tuple[str, float]]) -> List[str]:
    """Sort keys by score descending (frequent/recent first). Stable: equal
    scores keep input order. Input is (key, score) pairs; output is keys."""
    return [k for k, _ in sorted(scored, key=lambda kv: -kv[1])]
