import sys
from pathlib import Path

# Ensure the project root and scripts directory are on sys.path
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from scripts.main_entry_point import main
except ImportError:
    from main_entry_point import main

if __name__ == "__main__":
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(initial_file)
