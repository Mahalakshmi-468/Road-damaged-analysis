import uvicorn
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"======================================================")
    print(f"  ROADGUARD AI — Intelligent Road Damage Detection")
    print(f"  Starting API Server at http://{host}:{port}")
    print(f"  Interactive OpenAPI Docs: http://{host}:{port}/docs")
    print(f"======================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
