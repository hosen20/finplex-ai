import sys
from pathlib import Path

MODEL_SERVER_DIR = Path(__file__).resolve().parents[1]

if str(MODEL_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_SERVER_DIR))