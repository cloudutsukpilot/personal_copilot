import argparse

# Parse args once, at top level
parser = argparse.ArgumentParser()
parser.add_argument("--debug", default="false", help="Enable debug logging")
args = parser.parse_args()

DEBUG_MODE = args.debug.lower() == "true"

def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)
