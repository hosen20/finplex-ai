import sys
from pathlib import Path

WORKERS_ROOT = Path(__file__).resolve().parents[1]

if str(WORKERS_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKERS_ROOT))