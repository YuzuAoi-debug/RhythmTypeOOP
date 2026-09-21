# Marks scripts as a Python package and ensures project directories are on sys.path
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_BASE_DIR = _SCRIPTS_DIR.parent

if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
