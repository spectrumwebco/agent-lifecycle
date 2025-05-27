"""
API module for the Python agent.

This module provides FastAPI routes for the Python agent.
"""

from fastapi import APIRouter

from .langgraph import router as langgraph_router
from .neovim import router as neovim_router

api_router = APIRouter()

api_router.include_router(langgraph_router)
api_router.include_router(neovim_router)

__all__ = ["api_router"]
