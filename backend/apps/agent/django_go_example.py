"""
Example module demonstrating how to use the Go runtime integration in Django.
This module provides examples for executing tasks, managing state, and handling events.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .go_integration import get_go_runtime_integration

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def execute_task(request):
    """
    Django view for executing a task in the Go runtime.
    
    Example request:
    {
        "task_type": "example_task",
        "input": {
            "param1": "value1",
            "param2": "value2"
        },
        "agent_id": "agent1",
        "description": "Example task execution"
    }
    """
    try:
        data = json.loads(request.body)
        
        task_type = data.get("task_type")
        input_data = data.get("input", {})
        agent_id = data.get("agent_id")
        description = data.get("description")
        
        if not task_type:
            return JsonResponse({"error": "task_type is required"}, status=400)
        
        go_runtime = get_go_runtime_integration()
        
        result = go_runtime.execute_task(
            task_type=task_type,
            input_data=input_data,
            agent_id=agent_id,
            description=description
        )
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def execute_agent_task(request):
    """
    Django view for executing a task using a specific agent in the multi-agent system.
    
    Example request:
    {
        "agent_id": "agent1",
        "task_type": "example_task",
        "input": {
            "param1": "value1",
            "param2": "value2"
        },
        "description": "Example agent task execution"
    }
    """
    try:
        data = json.loads(request.body)
        
        agent_id = data.get("agent_id")
        task_type = data.get("task_type")
        input_data = data.get("input", {})
        description = data.get("description")
        
        if not agent_id:
            return JsonResponse({"error": "agent_id is required"}, status=400)
        
        if not task_type:
            return JsonResponse({"error": "task_type is required"}, status=400)
        
        go_runtime = get_go_runtime_integration()
        
        result = go_runtime.execute_agent_task(
            agent_id=agent_id,
            task_type=task_type,
            input_data=input_data,
            description=description
        )
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error executing agent task: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def manage_state(request, key=None):
    """
    Django view for managing state in the Go runtime.
    
    GET: Get a value from the shared state
    POST: Set a value in the shared state
    DELETE: Delete a value from the shared state
    """
    go_runtime = get_go_runtime_integration()
    
    try:
        if request.method == "GET":
            if not key:
                return JsonResponse({"error": "key is required"}, status=400)
            
            value = go_runtime.get_state(key)
            
            return JsonResponse({"key": key, "value": value})
        
        elif request.method == "POST":
            data = json.loads(request.body)
            
            key = data.get("key")
            value = data.get("value")
            
            if not key:
                return JsonResponse({"error": "key is required"}, status=400)
            
            success = go_runtime.set_state(key, value)
            
            return JsonResponse({"success": success})
        
        elif request.method == "DELETE":
            if not key:
                return JsonResponse({"error": "key is required"}, status=400)
            
            success = go_runtime.delete_state(key)
            
            return JsonResponse({"success": success})
        
        return JsonResponse({"error": "Method not allowed"}, status=405)
    except Exception as e:
        logger.error(f"Error managing state: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def publish_event(request):
    """
    Django view for publishing an event.
    
    Example request:
    {
        "event_type": "example_event",
        "data": {
            "param1": "value1",
            "param2": "value2"
        },
        "source": "django_view",
        "metadata": {
            "meta1": "value1",
            "meta2": "value2"
        }
    }
    """
    try:
        data = json.loads(request.body)
        
        event_type = data.get("event_type")
        event_data = data.get("data", {})
        source = data.get("source", "django_view")
        metadata = data.get("metadata")
        
        if not event_type:
            return JsonResponse({"error": "event_type is required"}, status=400)
        
        go_runtime = get_go_runtime_integration()
        
        success = go_runtime.publish_event(
            event_type=event_type,
            data=event_data,
            source=source,
            metadata=metadata
        )
        
        return JsonResponse({"success": success})
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
        return JsonResponse({"error": str(e)}, status=500)

def subscribe_to_example_events():
    """
    Example function demonstrating how to subscribe to events.
    This would typically be called during application startup.
    """
    go_runtime = get_go_runtime_integration()
    
    def handle_example_event(event_data):
        logger.info(f"Received example event: {event_data}")
    
    subscription_id = go_runtime.subscribe_to_events("example_event", handle_example_event)
    
    logger.info(f"Subscribed to example events with subscription ID: {subscription_id}")
    
    return subscription_id

"""

from django.urls import path
from . import django_go_example

urlpatterns = [
    path('api/go/task', django_go_example.execute_task, name='execute_task'),
    path('api/go/agent-task', django_go_example.execute_agent_task, name='execute_agent_task'),
    path('api/go/state/<str:key>', django_go_example.manage_state, name='manage_state'),
    path('api/go/state', django_go_example.manage_state, name='manage_state_no_key'),
    path('api/go/event', django_go_example.publish_event, name='publish_event'),
]
"""

"""

from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'your_app'
    
    def ready(self):
        from .django_go_example import subscribe_to_example_events
        
        subscribe_to_example_events()
"""
