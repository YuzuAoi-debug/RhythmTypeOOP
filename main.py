import sys
from pathlib import Path

# Ensure the scripts directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from main_entry_point import main

if __name__ == "__main__":
    main()
