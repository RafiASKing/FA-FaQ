"""
Application Kernel - FastAPI App Factory dengan Lifespan Manager.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings, paths
from core.logger import log
from app.services import WhatsAppService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager untuk startup dan shutdown events.
    """
    # === STARTUP ===
    log("🚀 Application Starting...")
    
    # Generate WA token jika dalam mode bot
    if hasattr(app.state, 'is_bot_mode') and app.state.is_bot_mode:
        log(f"🤖 Bot Mode: Identities Loaded: {len(settings.bot_identity_list)}")
        WhatsAppService.generate_token()
        
        # Start session dengan webhook URL
        webhook_url = "http://faq-bot:8000/webhook/whatsapp"
        WhatsAppService.start_session(webhook_url)
    
    log("✅ Application Ready!")
    
    yield
    
    # === SHUTDOWN ===
    log("👋 Application Shutting Down...")


def create_app(
    title: str = "Hospital FAQ API",
    description: str = "Semantic Search Knowledge Base for Hospital EMR",
    version: str = "2.0.0",
    include_bot_routes: bool = False,
    include_web_routes: bool = False
) -> FastAPI:
    """
    Factory function untuk membuat FastAPI application.
    
    Args:
        title: Judul API
        description: Deskripsi API
        version: Versi API
        include_bot_routes: Include WhatsApp bot routes
        include_web_routes: Include Web V2 routes
        
    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Store mode in state
    app.state.is_bot_mode = include_bot_routes
    
    # === CORS Middleware ===
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # === Static Files ===
    # Mount images directory
    app.mount(
        "/images",
        StaticFiles(directory=str(paths.IMAGES_DIR)),
        name="images"
    )
    
    # === Register Routes ===
    from app.controllers.search_controller import router as search_router
    from app.controllers.faq_controller import router as faq_router
    
    # API Routes
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(faq_router, prefix="/api/v1")
    
    # Bot Routes (Webhook)
    if include_bot_routes:
        from app.controllers.webhook_controller import router as webhook_router
        app.include_router(webhook_router)
    
    # Web V2 Routes (HTML Templates)
    if include_web_routes:
        from routes.web import router as web_router
        app.include_router(web_router)
        
        # Mount static files untuk web
        app.mount(
            "/static",
            StaticFiles(directory=str(paths.STATIC_DIR)),
            name="static"
        )
    
    # === Health Check ===
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": version}
    
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint dengan info API."""
        return {
            "name": title,
            "version": version,
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


# Pre-configured app instances
def create_api_app() -> FastAPI:
    """Create API-only application."""
    return create_app(
        title="Hospital FAQ API",
        description="RESTful API for FAQ Knowledge Base",
        include_bot_routes=False,
        include_web_routes=False
    )


def create_bot_app() -> FastAPI:
    """Create WhatsApp Bot application."""
    return create_app(
        title="Hospital FAQ Bot",
        description="WhatsApp Bot for FAQ",
        include_bot_routes=True,
        include_web_routes=False
    )


def create_web_app() -> FastAPI:
    """Create Web application with HTML templates."""
    return create_app(
        title="Hospital FAQ Web",
        description="Web Interface for FAQ",
        include_bot_routes=False,
        include_web_routes=True
    )
