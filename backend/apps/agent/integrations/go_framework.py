"""
Django integration with the Kled.io Go Framework.

This module provides integration between Django and the Go Framework,
implementing shared state management and API communication.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional, List, Union
from django.conf import settings
from django.utils.module_loading import import_string
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class GoFrameworkClient:
    """
    Client for communicating with the Kled.io Go Framework.
    
    This client handles API communication and shared state management
    between Django and the Go Framework.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the Go Framework client.
        
        Args:
            base_url: Base URL for the Go Framework API. If not provided,
                     it will be read from Django settings.
        """
        self.base_url = base_url or getattr(settings, 'GO_FRAMEWORK_URL', 'http://localhost:8080')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        auth_token = getattr(settings, 'GO_FRAMEWORK_AUTH_TOKEN', None)
        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}',
            })
    
    def register_model(self, name: str, fields: Dict[str, str]) -> Dict[str, Any]:
        """
        Register a Django model with the Go Framework.
        
        Args:
            name: Name of the model
            fields: Dictionary mapping field names to field types
            
        Returns:
            Response from the Go Framework
        """
        url = f"{self.base_url}/api/django/models"
        data = {
            "name": name,
            "fields": fields,
        }
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to register model with Go Framework: {e}")
            return {"error": str(e)}
    
    def register_route(self, path: str, method: str, handler_name: str) -> Dict[str, Any]:
        """
        Register a Django route with the Go Framework.
        
        Args:
            path: URL path for the route
            method: HTTP method (GET, POST, PUT, DELETE)
            handler_name: Name of the handler function
            
        Returns:
            Response from the Go Framework
        """
        url = f"{self.base_url}/api/django/routes"
        data = {
            "path": path,
            "method": method,
            "handler": handler_name,
        }
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to register route with Go Framework: {e}")
            return {"error": str(e)}
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get the shared context from the Go Framework.
        
        Returns:
            Shared context dictionary
        """
        url = f"{self.base_url}/api/django/context"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get context from Go Framework: {e}")
            return {}
    
    def update_context(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the shared context in the Go Framework.
        
        Args:
            updates: Dictionary of context updates
            
        Returns:
            Updated context
        """
        url = f"{self.base_url}/api/django/context"
        
        try:
            response = self.session.patch(url, json=updates)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to update context in Go Framework: {e}")
            return {"error": str(e)}
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool in the Go Framework.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        url = f"{self.base_url}/api/tools/{tool_name}"
        
        try:
            response = self.session.post(url, json=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to execute tool in Go Framework: {e}")
            return {"error": str(e)}


class SharedStateConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for shared state between Django and Go Framework.
    
    This consumer handles real-time communication for shared state updates
    between Django and the Go Framework.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.group_name = "shared_state"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        
        Args:
            text_data: JSON string with state updates
        """
        try:
            data = json.loads(text_data)
            
            client = GoFrameworkClient()
            client.update_context(data)
            
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "state_update",
                    "data": data
                }
            )
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    async def state_update(self, event):
        """
        Send state update to WebSocket.
        
        Args:
            event: Event containing state update data
        """
        data = event["data"]
        
        await self.send(text_data=json.dumps(data))


class GoFrameworkMiddleware:
    """
    Django middleware for Go Framework integration.
    
    This middleware synchronizes shared state between Django and Go Framework
    for each request.
    """
    
    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
        self.client = GoFrameworkClient()
    
    def __call__(self, request):
        """Process request and synchronize shared state."""
        context = self.client.get_context()
        request.go_framework_context = context
        
        response = self.get_response(request)
        
        if hasattr(request, 'go_framework_context_updates'):
            self.client.update_context(request.go_framework_context_updates)
        
        return response


def update_shared_state(request, updates):
    """
    Update shared state for the current request.
    
    Args:
        request: Django request object
        updates: Dictionary of state updates
    """
    if not hasattr(request, 'go_framework_context_updates'):
        request.go_framework_context_updates = {}
    
    request.go_framework_context_updates.update(updates)


def register_django_models():
    """
    Register all Django models with the Go Framework.
    
    This function should be called during Django startup to register
    all models with the Go Framework.
    """
    from django.apps import apps
    
    client = GoFrameworkClient()
    
    for model in apps.get_models():
        fields = {}
        for field in model._meta.fields:
            fields[field.name] = field.get_internal_type()
        
        client.register_model(model._meta.model_name, fields)


def register_django_routes():
    """
    Register Django routes with the Go Framework.
    
    This function should be called during Django startup to register
    all routes with the Go Framework.
    """
    from django.urls import get_resolver
    
    client = GoFrameworkClient()
    resolver = get_resolver()
    
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'pattern'):
            path = str(pattern.pattern)
            if hasattr(pattern, 'callback') and pattern.callback:
                handler_name = f"{pattern.callback.__module__}.{pattern.callback.__name__}"
                client.register_route(path, "GET", handler_name)
