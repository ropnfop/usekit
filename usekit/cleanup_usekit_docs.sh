#!/bin/bash
# cleanup_usekit_docs.sh — Remove Claude Code duplicates from usekit docs
# Run from: /storage/emulated/0/DEV/project/usekit
# Safe: only removes confirmed duplicates

echo "◆ usekit docs Cleanup"
echo "──────────────────────────────────────"

# 1. Remove docs/manual/ (exact duplicate of docs/sub/manual/usekit_guide/)
if [ -d "docs/manual" ]; then
  rm -rf docs/manual
  echo "  ✓ Removed docs/manual/ (duplicate of docs/sub/manual/usekit_guide/)"
fi

# 2. Remove CLAUDE_USEKIT_LOCAL_ALIAS.md (823-line duplicate of CLAUDE.md content)
if [ -f "docs/base/CLAUDE_USEKIT_LOCAL_ALIAS.md" ]; then
  rm docs/base/CLAUDE_USEKIT_LOCAL_ALIAS.md
  echo "  ✓ Removed docs/base/CLAUDE_USEKIT_LOCAL_ALIAS.md (duplicate)"
fi

echo ""
echo "◆ Cleanup complete"
echo "──────────────────────────────────────"
