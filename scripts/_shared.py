"""Load deployment utilities from the pinned core or a standalone release."""
import importlib.util
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == 'scripts' else SCRIPT_DIR
CORE = ROOT / 'vendor/holepunch'
SHARED = CORE / 'scripts' if (CORE / 'scripts' / 'deploy.py').is_file() else ROOT / 'shared'


def load(name):
    sys.path.insert(0, str(SHARED))
    spec = importlib.util.spec_from_file_location('holepunch_shared_' + name, SHARED / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
