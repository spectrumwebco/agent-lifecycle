from django.http import JsonResponse
import traceback

from apps.agent.agent_framework.runtime.abstract import _ExceptionTransfer


class AgentFrameworkExceptionMiddleware:
    """Middleware to handle agent framework exceptions."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            if hasattr(exc, 'status_code'):
                status = getattr(exc, 'status_code', 500)
                return JsonResponse(
                    {"detail": str(exc)}, status=status
                )
            
            extra_info = getattr(exc, "extra_info", {})
            _exc = _ExceptionTransfer(
                message=str(exc),
                class_path=type(exc).__module__ + "." + type(exc).__name__,
                traceback=traceback.format_exc(),
                extra_info=extra_info,
            )
            return JsonResponse(
                {"agent_frameworkception": _exc.model_dump()}, status=511
            )
