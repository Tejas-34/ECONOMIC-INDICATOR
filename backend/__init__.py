"""Economics Indicator Dashboard Backend Package."""
import sys
from pathlib import Path

_root_dir = str(Path(__file__).resolve().parent.parent)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
