"""
Base Django integration for Python agents.

This module provides base Django integration components that can be used by both
Kled and Veigar agents.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)

class BaseAgentView:
    """Base view for agent integration with Django."""
    
    def __init__(self, agent_name: str):
        """
        Initialize the base agent view.
        
        Args:
            agent_name: Name of the agent.
        """
        self.agent_name = agent_name
        logger.info(f"Initialized {agent_name} agent view")
    
    def handle_request(self, request: HttpRequest) -> HttpResponse:
        """
        Handle a Django request.
        
        Args:
            request: Django HTTP request.
            
        Returns:
            Django HTTP response.
        """
        method = request.method.lower() if request.method else "get"
        handler = getattr(self, f"handle_{method}", None)
        
        if handler is None:
            return JsonResponse({
                "success": False,
                "message": f"Method {request.method} not allowed"
            }, status=405)
        
        try:
            return handler(request)
        except Exception as e:
            logger.exception(f"Error handling {request.method} request")
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=500)
    
    def handle_get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle a GET request.
        
        Args:
            request: Django HTTP request.
            
        Returns:
            Django HTTP response.
        """
        return JsonResponse({
            "success": False,
            "message": "GET method not implemented"
        }, status=501)
    
    def handle_post(self, request: HttpRequest) -> HttpResponse:
        """
        Handle a POST request.
        
        Args:
            request: Django HTTP request.
            
        Returns:
            Django HTTP response.
        """
        return JsonResponse({
            "success": False,
            "message": "POST method not implemented"
        }, status=501)
    
    def handle_put(self, request: HttpRequest) -> HttpResponse:
        """
        Handle a PUT request.
        
        Args:
            request: Django HTTP request.
            
        Returns:
            Django HTTP response.
        """
        return JsonResponse({
            "success": False,
            "message": "PUT method not implemented"
        }, status=501)
    
    def handle_delete(self, request: HttpRequest) -> HttpResponse:
        """
        Handle a DELETE request.
        
        Args:
            request: Django HTTP request.
            
        Returns:
            Django HTTP response.
        """
        return JsonResponse({
            "success": False,
            "message": "DELETE method not implemented"
        }, status=501)

class BaseAgentMiddleware:
    """Base middleware for agent integration with Django."""
    
    def __init__(self, get_response, agent_name: str):
        """
        Initialize the base agent middleware.
        
        Args:
            get_response: Django get_response function.
            agent_name: Name of the agent.
        """
        self.get_response = get_response
        self.agent_name = agent_name
        logger.info(f"Initialized {agent_name} agent middleware")
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process a Django request.
        
        Args:
            request: Django HTTP request.
            
        Returns:
            Django HTTP response.
        """
        self.process_request(request)
        
        response = self.get_response(request)
        
        self.process_response(request, response)
        
        return response
    
    def process_request(self, request: HttpRequest) -> None:
        """
        Process a request before it is handled by a view.
        
        Args:
            request: Django HTTP request.
        """
        pass
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> None:
        """
        Process a response after it is returned by a view.
        
        Args:
            request: Django HTTP request.
            response: Django HTTP response.
        """
        pass

def register_agent_urls(urlpatterns: List, agent_views: Dict[str, BaseAgentView], prefix: str = '') -> None:
    """
    Register agent views with Django URL patterns.
    
    Args:
        urlpatterns: Django URL patterns list.
        agent_views: Dictionary mapping URL paths to agent views.
        prefix: URL prefix for all agent views.
    """
    from django.urls import path
    
    for url_path, view in agent_views.items():
        full_path = f"{prefix}/{url_path}".lstrip('/')
        urlpatterns.append(
            path(full_path, view.handle_request)
        )
        
    logger.info(f"Registered {len(agent_views)} agent URLs with prefix '{prefix}'")
