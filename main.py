"""Unified entry point for Twelve-YinXi: The Bird Council.

Usage:
    python main.py

This will:
1. Initialize SQLite database
2. Start FastAPI server
3. Open browser automatically
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / "backend" / ".env")

from app.core.config import settings


def main():
    """Main entry point."""
    print("Starting Twelve-YinXi: The Bird Council...")
    print(f"Database: {settings.DB_PATH}")
    print(f"Server: http://{settings.HOST}:{settings.PORT}\n")

    # Start FastAPI server
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,  # Set to True for development
        log_level="info",
    )


if __name__ == "__main__":
    main()
