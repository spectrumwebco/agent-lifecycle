from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import asyncio
import os

from apps.agent.agent_framework.shared.runtime import (
    Action,
    BashAction,
    Command,
    CreateBashSessionRequest,
    CreateSessionRequest,
)
from apps.agent.agent_framework.runtime.local import LocalRuntime

logger = logging.getLogger(__name__)
runtime = LocalRuntime()


def run_async(coroutine):
    """Run an async function in a synchronous context."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


def serialize_model(model):
    """Serialize a Pydantic model to a dictionary."""
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


@csrf_exempt
@require_http_methods(["POST"])
def run_agent_view(request):
    """
    Django view to run the agent with the provided configuration.
    """
    try:
        data = json.loads(request.body)

        bash_session_request = CreateBashSessionRequest(
            working_directory=data.get("working_directory", os.getcwd()),
            session_id=data.get("session_id", None),
        )
        session_response = run_async(runtime.create_session(bash_session_request))
        session_id = session_response.session_id

        command_str = data.get("command", "")
        
        action = BashAction(
            session=session_id,
            command=command_str,
            action_type="bash"
        )
        result = run_async(runtime.run_in_session(action))

        return JsonResponse(
            {"status": "success", "session_id": session_id, "result": serialize_model(result)}
        )
    except Exception as e:
        logger.exception("Error running agent")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
