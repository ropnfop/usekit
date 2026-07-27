#!/usr/bin/env bash
# cleanup.sh — remove the orphaned util/emo/ location from the earlier patch.
#
# Context: the FIRST EMO patch placed the module under util/emo/ (as uu.hslva).
# We moved it to its own namespace (init/emo/ as ue.hslva), so util/emo/ is now
# orphaned. This script removes it ONLY if present. Safe to run even if you
# never applied the first patch (it will just report nothing to do).
#
# Run from the usekit PACKAGE dir (the one holding usemain.py):
#     bash cleanup.sh
# (Termux/Android friendly: existence checks + echo, no globs that bite.)

set -u

ORPHAN="classes/support/base/init/util/emo"

echo "── EMO cleanup ──────────────────────────────"

if [ -d "$ORPHAN" ]; then
    echo "  found orphan: $ORPHAN"
    rm -rf "$ORPHAN"
    if [ -d "$ORPHAN" ]; then
        echo "  ✗ FAILED to remove (check permissions): $ORPHAN"
    else
        echo "  ✓ removed: $ORPHAN"
    fi
else
    echo "  · nothing to do (orphan not present): $ORPHAN"
fi

# stray bytecode for the old module path, if any
PYC="classes/support/base/init/util/__pycache__"
if [ -d "$PYC" ]; then
    # only the sbi_util bytecode could be stale; refreshed automatically on import,
    # but clear it to be safe.
    rm -f "$PYC"/sbi_util.*.pyc 2>/dev/null && echo "  · cleared stale sbi_util bytecode"
fi

echo "─────────────────────────────────────────────"
echo "  done. (uu is reverted to task/queue only; emo lives at init/emo as ue.)"
