"""
Swagger documentation for the Neovim API service.

This module provides Swagger documentation for the Neovim API service.
"""

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema for Swagger documentation.
    
    Args:
        app: FastAPI application
        
    Returns:
        dict: OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Neovim API",
        version="1.0.0",
        description="API for interacting with Neovim instances in the agent runtime",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    openapi_schema["info"]["contact"] = {
        "name": "Spectrum Web Co",
        "url": "https://spectrumwebco.com",
        "email": "support@spectrumwebco.com",
    }
    
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8090",
            "description": "Local development server",
        },
        {
            "url": "http://185.196.220.224:8090",
            "description": "Production server",
        },
    ]
    
    openapi_schema["tags"] = [
        {
            "name": "neovim",
            "description": "Operations related to Neovim instances",
        },
    ]
    
    openapi_schema["externalDocs"] = {
        "description": "Neovim API Documentation",
        "url": "https://spectrumwebco.com/docs/neovim-api",
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
