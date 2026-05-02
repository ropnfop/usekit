"""Entry point wrapper. Sets USEKIT_QUIET before any usekit import."""
import os
os.environ["USEKIT_QUIET"] = "1"

def run():
    from usekit.cli.main import main
    import sys
    sys.exit(main())

if __name__ == "__main__":
    run()
