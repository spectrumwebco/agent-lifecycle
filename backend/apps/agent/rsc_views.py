"""
Django views for React Server Components (RSC) integration.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .rsc_integration import get_rsc_integration

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def generate_component(request: HttpRequest) -> JsonResponse:
    """
    Generate a React Server Component.
    
    Example request:
    {
        "component_type": "button",
        "props": {
            "label": "Click me",
            "variant": "primary",
            "onClick": "handleClick"
        }
    }
    """
    try:
        data = json.loads(request.body)
        
        component_type = data.get("component_type")
        props = data.get("props", {})
        
        if not component_type:
            return JsonResponse({"error": "component_type is required"}, status=400)
        
        rsc_integration = get_rsc_integration()
        
        component_id = rsc_integration.generate_component(component_type, props)
        
        if component_id is None:
            return JsonResponse({"error": "Failed to generate component"}, status=500)
        
        component = rsc_integration.get_component(component_id)
        
        return JsonResponse({
            "component_id": component_id,
            "component": component
        })
    except Exception as e:
        logger.error(f"Error generating component: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def generate_component_from_agent_action(request: HttpRequest) -> JsonResponse:
    """
    Generate a React Server Component from an agent action.
    
    Example request:
    {
        "agent_id": "agent1",
        "action_id": "action1",
        "action_type": "thinking",
        "action_data": {
            "thought": "I need to analyze this code..."
        }
    }
    """
    try:
        data = json.loads(request.body)
        
        agent_id = data.get("agent_id")
        action_id = data.get("action_id")
        action_type = data.get("action_type")
        action_data = data.get("action_data", {})
        
        if not agent_id:
            return JsonResponse({"error": "agent_id is required"}, status=400)
        
        if not action_id:
            return JsonResponse({"error": "action_id is required"}, status=400)
        
        if not action_type:
            return JsonResponse({"error": "action_type is required"}, status=400)
        
        rsc_integration = get_rsc_integration()
        
        component_id = rsc_integration.generate_component_from_agent_action(
            agent_id, action_id, action_type, action_data
        )
        
        if component_id is None:
            return JsonResponse({"error": "Failed to generate component from agent action"}, status=500)
        
        component = rsc_integration.get_component(component_id)
        
        return JsonResponse({
            "component_id": component_id,
            "component": component
        })
    except Exception as e:
        logger.error(f"Error generating component from agent action: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def generate_component_from_tool_usage(request: HttpRequest) -> JsonResponse:
    """
    Generate a React Server Component from a tool usage.
    
    Example request:
    {
        "agent_id": "agent1",
        "tool_id": "tool1",
        "tool_name": "code_generator",
        "tool_input": {
            "language": "python",
            "task": "Generate a function to calculate Fibonacci numbers"
        },
        "tool_output": {
            "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        }
    }
    """
    try:
        data = json.loads(request.body)
        
        agent_id = data.get("agent_id")
        tool_id = data.get("tool_id")
        tool_name = data.get("tool_name")
        tool_input = data.get("tool_input", {})
        tool_output = data.get("tool_output", {})
        
        if not agent_id:
            return JsonResponse({"error": "agent_id is required"}, status=400)
        
        if not tool_id:
            return JsonResponse({"error": "tool_id is required"}, status=400)
        
        if not tool_name:
            return JsonResponse({"error": "tool_name is required"}, status=400)
        
        rsc_integration = get_rsc_integration()
        
        component_id = rsc_integration.generate_component_from_tool_usage(
            agent_id, tool_id, tool_name, tool_input, tool_output
        )
        
        if component_id is None:
            return JsonResponse({"error": "Failed to generate component from tool usage"}, status=500)
        
        component = rsc_integration.get_component(component_id)
        
        return JsonResponse({
            "component_id": component_id,
            "component": component
        })
    except Exception as e:
        logger.error(f"Error generating component from tool usage: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_component(request: HttpRequest, component_id: str) -> JsonResponse:
    """
    Get a component by ID.
    """
    try:
        rsc_integration = get_rsc_integration()
        
        component = rsc_integration.get_component(component_id)
        
        if component is None:
            return JsonResponse({"error": f"Component not found: {component_id}"}, status=404)
        
        return JsonResponse({
            "component": component
        })
    except Exception as e:
        logger.error(f"Error getting component: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_components(request: HttpRequest) -> JsonResponse:
    """
    List all components.
    """
    try:
        rsc_integration = get_rsc_integration()
        
        components = rsc_integration.list_components()
        
        return JsonResponse({
            "components": components
        })
    except Exception as e:
        logger.error(f"Error listing components: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_components_by_agent(request: HttpRequest, agent_id: str) -> JsonResponse:
    """
    Get all components for an agent.
    """
    try:
        rsc_integration = get_rsc_integration()
        
        components = rsc_integration.get_components_by_agent(agent_id)
        
        return JsonResponse({
            "components": components
        })
    except Exception as e:
        logger.error(f"Error getting components by agent: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_components_by_tool(request: HttpRequest, tool_id: str) -> JsonResponse:
    """
    Get all components for a tool.
    """
    try:
        rsc_integration = get_rsc_integration()
        
        components = rsc_integration.get_components_by_tool(tool_id)
        
        return JsonResponse({
            "components": components
        })
    except Exception as e:
        logger.error(f"Error getting components by tool: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def stream_components(request: HttpRequest) -> StreamingHttpResponse:
    """
    Stream components as Server-Sent Events (SSE).
    """
    def event_stream():
        rsc_integration = get_rsc_integration()
        
        components = rsc_integration.list_components()
        for component in components:
            component_json = json.dumps(component)
            yield f"data: {component_json}\n\n"
        
        
        import time
        while True:
            yield f"data: {{'type': 'ping', 'timestamp': {int(time.time())}}}\n\n"
            time.sleep(30)
    
    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
