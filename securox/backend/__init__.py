# Securox Backend Package
import sys
from pathlib import Path
app_dir = Path(__file__).resolve().parent / 'app'
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Alias backend.ml to backend.app.ai / ml
from .app import ai as ml
from .app import services
from .app import assets
