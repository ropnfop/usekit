"""Allow `python -m usekit.cli` and serve as entry point."""
import os
os.environ["USEKIT_QUIET"] = "1"

from usekit.cli.main import main
import sys
sys.exit(main())
