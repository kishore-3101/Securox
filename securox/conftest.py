import sys
from pathlib import Path

# Add securox/backend/app to sys.path so 'import main' or 'from core import ...' works
backend_app = Path(__file__).resolve().parent / "backend" / "app"
if str(backend_app) not in sys.path:
    sys.path.insert(0, str(backend_app))

securox_root = Path(__file__).resolve().parent
if str(securox_root) not in sys.path:
    sys.path.insert(0, str(securox_root))
