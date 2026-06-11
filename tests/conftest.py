import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
API_SERVICE_DIR = ROOT_DIR / "services" / "api"

if str(API_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_DIR))