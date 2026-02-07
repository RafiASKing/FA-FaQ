"""
Route Registration - Centralized route setup following Siloam convention.
All route/static-file mounting lives here, keeping Kernel.py clean.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config.settings import paths


def setup_routes(
    app: FastAPI,
    include_bot_routes: bool = False,
    include_web_routes: bool = False,
):
    """
    Register all routes and static mounts on the FastAPI app.

    Args:
        app: FastAPI application instance.
        include_bot_routes: Include WhatsApp webhook routes.
        include_web_routes: Include Web V2 HTML template routes.
    """
    # === Static Files (always mounted) ===
    app.mount(
        "/images",
        StaticFiles(directory=str(paths.IMAGES_DIR)),
        name="images",
    )

    # === API v1 routes (aggregated from controllers) ===
    from routes.api.v1 import router as api_v1_router
    app.include_router(api_v1_router)

    # === Bot Routes (Webhook) ===
    if include_bot_routes:
        from app.controllers.webhook_controller import router as webhook_router
        app.include_router(webhook_router)

    # === Web V2 Routes (HTML Templates) ===
    if include_web_routes:
        from routes.web import router as web_router
        app.include_router(web_router)

        app.mount(
            "/static",
            StaticFiles(directory=str(paths.STATIC_DIR)),
            name="static",
        )

    # === Utility Endpoints ===
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": app.version}

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint dengan info API."""
        return {
            "name": app.title,
            "version": app.version,
            "docs": "/docs",
            "health": "/health",
        }
