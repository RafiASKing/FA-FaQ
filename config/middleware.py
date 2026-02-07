"""
Middleware Setup - Following Siloam convention: config/middleware.py
"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def setup_middleware(app: FastAPI):
    """Configure all middleware for the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
