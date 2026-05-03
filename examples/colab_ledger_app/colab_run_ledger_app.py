"""
Minimal Colab runner for the generated ledger app.

Run this after:

1. mounting Google Drive
2. installing USEKIT
3. running use.colab()
4. generating the ledger app with examples/ledger_app/ledger_app_builder.py
"""

from usekit import use

use.exec.pyp.base("examples.ledger_app.main")
