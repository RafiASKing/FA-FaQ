"""
Application Kernel - FastAPI App Factory dengan Lifespan Manager.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import container
from config.settings import settings
from config.routes import setup_routes
from config.middleware import setup_middleware
from core.logger import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager untuk startup dan shutdown events.
    Preload shared resources agar user pertama tidak kena cold-start.
    """
    # === STARTUP ===
    log("Application Starting...")

    # Preload shared resources
    log("Preloading vector store...")
    container.get_vector_store()
    log("Vector store ready.")

    log("Preloading embedding engine...")
    container.get_embedding()
    log("Embedding engine ready.")

    log("Preloading LLM engine...")
    container.get_llm()
    log("LLM engine ready.")

    # Initialize messaging jika dalam mode bot
    if hasattr(app.state, 'is_bot_mode') and app.state.is_bot_mode:
        log(f"Bot Mode: Identities Loaded: {len(settings.bot_identity_list)}")

        webhook_url = "http://faq-bot:8000/webhook/whatsapp"
        container.get_messaging().initialize(webhook_url=webhook_url)

    log("Application Ready!")

    yield

    # === SHUTDOWN ===
    log("Application Shutting Down...")


def create_app(
    title: str = "Hospital FAQ API",
    description: str = "Semantic Search Knowledge Base for Hospital EMR",
    version: str = "2.0.0",
    include_bot_routes: bool = False,
    include_web_routes: bool = False
) -> FastAPI:
    """Factory function untuk membuat FastAPI application."""
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    app.state.is_bot_mode = include_bot_routes

    setup_middleware(app)
    setup_routes(app, include_bot_routes, include_web_routes)

    return app


# Pre-configured app instances
def create_api_app() -> FastAPI:
    """Create API-only application."""
    return create_app(
        title="Hospital FAQ API",
        description="RESTful API for FAQ Knowledge Base",
    )


def create_bot_app() -> FastAPI:
    """Create WhatsApp Bot application."""
    return create_app(
        title="Hospital FAQ Bot",
        description="WhatsApp Bot for FAQ",
        include_bot_routes=True,
    )


def create_web_app() -> FastAPI:
    """Create Web application with HTML templates."""
    return create_app(
        title="Hospital FAQ Web",
        description="Web Interface for FAQ",
        include_web_routes=True,
    )
