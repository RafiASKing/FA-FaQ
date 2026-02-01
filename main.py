"""
Main Entry Point - Bootstrap untuk semua aplikasi.

Usage:
    # API Server
    python main.py api
    
    # WhatsApp Bot
    python main.py bot
    
    # Web V2 (HTML)
    python main.py web
    
    # Atau langsung dengan uvicorn:
    uvicorn main:api_app --host 0.0.0.0 --port 8000
    uvicorn main:bot_app --host 0.0.0.0 --port 8000
    uvicorn main:web_app --host 0.0.0.0 --port 8080
"""

import sys
import uvicorn

from app.Kernel import create_api_app, create_bot_app, create_web_app


# Pre-created app instances untuk uvicorn
api_app = create_api_app()
bot_app = create_bot_app()
web_app = create_web_app()


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run API server."""
    uvicorn.run(
        "main:api_app",
        host=host,
        port=port,
        reload=reload
    )


def run_bot(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run WhatsApp Bot server."""
    uvicorn.run(
        "main:bot_app",
        host=host,
        port=port,
        reload=reload
    )


def run_web(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """Run Web V2 server."""
    uvicorn.run(
        "main:web_app",
        host=host,
        port=port,
        reload=reload
    )


def print_usage():
    """Print usage information."""
    print("""
Hospital FAQ Application
========================

Usage: python main.py <command> [options]

Commands:
    api     Start API server (port 8000)
    bot     Start WhatsApp Bot server (port 8000)
    web     Start Web V2 server (port 8080)
    
Options:
    --reload    Enable auto-reload for development
    --port      Override default port
    
Examples:
    python main.py api
    python main.py bot --reload
    python main.py web --port 3000
    
Or use uvicorn directly:
    uvicorn main:api_app --host 0.0.0.0 --port 8000
    uvicorn main:bot_app --host 0.0.0.0 --port 8000
    uvicorn main:web_app --host 0.0.0.0 --port 8080

For Streamlit apps:
    streamlit run streamlit_apps/user_app.py --server.port 8501
    streamlit run streamlit_apps/admin_app.py --server.port 8502
    """)


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if not args:
        print_usage()
        sys.exit(0)
    
    command = args[0].lower()
    reload = "--reload" in args
    
    # Parse port if provided
    port = None
    for i, arg in enumerate(args):
        if arg == "--port" and i + 1 < len(args):
            try:
                port = int(args[i + 1])
            except ValueError:
                pass
    
    if command == "api":
        run_api(port=port or 8000, reload=reload)
    elif command == "bot":
        run_bot(port=port or 8000, reload=reload)
    elif command == "web":
        run_web(port=port or 8080, reload=reload)
    elif command in ["--help", "-h", "help"]:
        print_usage()
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)
