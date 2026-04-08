"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import webbrowser
import asyncio
from pathlib import Path

from .core.config import settings
from .core.database import init_db, backup_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    print("\n" + "=" * 50)
    print("Twelve-YinXi: The Bird Council")
    print("=" * 50)

    # Initialize database
    await init_db()

    # Check vector search status
    try:
        from .services.vector_search import HAS_VECTOR_SEARCH

        if HAS_VECTOR_SEARCH:
            print("[OK] Vector search: enabled")
        else:
            print("[WARN] Vector search: not installed (using text match)")
            print("[TIP] Install: pip install -r requirements-vector.txt")
    except ImportError:
        print("[WARN] Vector search: not installed (using text match)")

    print(f"\nServer: http://{settings.HOST}:{settings.PORT}")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")

    # Auto-open browser
    if settings.AUTO_OPEN_BROWSER:
        asyncio.create_task(open_browser())

    yield

    # Shutdown
    print("\nShutting down...")
    await backup_db()


async def open_browser():
    """Open browser after short delay."""
    await asyncio.sleep(1.5)
    webbrowser.open(f"http://{settings.HOST}:{settings.PORT}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Twelve-YinXi: The Bird Council",
        description="Multi-agent deliberation system with 23 seats",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    from .api import router

    app.include_router(router, prefix="/api/v1")

    # Serve frontend static files if they exist
    frontend_dist = Path(__file__).parent.parent.parent / "frontend-dist"
    if frontend_dist.exists():
        app.mount(
            "/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend"
        )

    return app


app = create_app()
