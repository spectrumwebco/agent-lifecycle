"""
LangGraph API routes for Veigar security agent.

This module provides LangGraph API routes for the Veigar security agent.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from backend.apps.agent.shared.django_integration.base import BaseAgentView
from backend.apps.agent.veigar.agent.run.run_security_review import run_security_review

logger = logging.getLogger(__name__)

class SecurityLangGraphView(BaseAgentView):
    """LangGraph API view for Veigar security agent."""
    
    def __init__(self):
        """Initialize the security LangGraph view."""
        super().__init__("veigar")
    
    def handle_post(self, request: HttpRequest) -> JsonResponse:
        """
        Handle a POST request to run a security review.
        
        Args:
            request: Django HTTP request.
            
        Returns:
            Django HTTP response.
        """
        try:
            data = json.loads(request.body)
            
            code = data.get("code")
            if not code:
                return JsonResponse({
                    "success": False,
                    "message": "Code is required"
                }, status=400)
            
            context = data.get("context", {})
            
            result = run_security_review(code, context)
            
            return JsonResponse({
                "success": True,
                "message": "Security review completed successfully",
                "result": result
            })
        except Exception as e:
            logger.exception("Error running security review")
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def security_review_api(request: HttpRequest) -> JsonResponse:
    """
    API endpoint for running a security review.
    
    Args:
        request: Django HTTP request.
        
    Returns:
        Django HTTP response.
    """
    view = SecurityLangGraphView()
    return view.handle_request(request)
