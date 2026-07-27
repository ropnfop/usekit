#!/usr/bin/env bash
# Clears stale bytecode so the 2-file patch takes effect (no dead files to remove).
set -e
cd "$(dirname "$0")"
echo "🧹 data keydata patch cleanup..."
find . -name "*.pyc" \( -path "*dbl_read*" -o -path "*dbl_common*" \) -delete 2>/dev/null || true
find . -name "__pycache__" -type d \( -path "*ops*" -o -path "*sub*" \) -exec rm -rf {} + 2>/dev/null || true
echo "✅ Done (bytecode cleared)."
