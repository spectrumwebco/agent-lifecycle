"""
Neovim API service for the Python agent.

This module provides a FastAPI service for interacting with Neovim instances.
"""

from .routes import router

__all__ = ["router"]
