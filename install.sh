#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "[usekit] Updating Termux packages..."
pkg update -y

echo "[usekit] Installing Python and pip..."
pkg install -y python python-pip

echo "[usekit] Upgrading pip..."
python -m pip install --upgrade pip

echo "[usekit] Installing usekit..."
pip install --upgrade usekit

echo "[usekit] Checking installation..."
python - <<'PY'
from usekit import use, u
print("[usekit] import OK")
use.check()
PY

echo ""
echo "[usekit] Installation complete."
echo ""
echo "Next steps:"
echo "  python"
echo "  from usekit import use"
echo "  use.termux()     # setup storage permission (first time only)"
echo "  from usekit import u"
echo "  u.editor()       # launch the mobile web editor"
