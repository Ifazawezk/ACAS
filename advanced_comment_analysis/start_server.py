#!/usr/bin/env python3
"""Start the FastAPI development server with proper path setup"""
import sys
import os
from pathlib import Path

# Add the project root to sys.path so app module can be found
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )
