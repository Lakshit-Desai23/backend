from pathlib import Path
import sys


local_deps = Path(__file__).resolve().parent / ".deps"
if local_deps.exists():
    sys.path.insert(0, str(local_deps))
