from pathlib import Path
import sys


deps_path = Path(__file__).resolve().parent / ".deps"
if deps_path.exists():
    sys.path.insert(0, str(deps_path))

import uvicorn


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
