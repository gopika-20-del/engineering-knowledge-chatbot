#!/usr/bin/env python
"""Backend server launcher with proper path setup"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Now import and run
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
