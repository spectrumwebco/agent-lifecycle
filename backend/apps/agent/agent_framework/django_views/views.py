import json
import shutil
import tempfile
import traceback
import zipfile
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agent.agent_framework import __version__
from apps.agent.agent_framework.runtime.abstract import (
    Action,
    CloseResponse,
    CloseSessionRequest,
    Command,
    CreateSessionRequest,
    ReadFileRequest,
    UploadResponse,
    WriteFileRequest,
    _ExceptionTransfer,
)
from apps.agent.agent_framework.runtime.local import LocalRuntime

runtime = LocalRuntime()


def serialize_model(model):
    """Serialize a Pydantic model to a dictionary."""
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


class AgentExceptionMiddleware:
    """Middleware to handle agent framework exceptions."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            if hasattr(exc, 'status_code'):
                return JsonResponse(
                    {"detail": str(exc)}, status=exc.status_code
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


@api_view(['GET'])
@permission_classes([])
@authentication_classes([])
def root(request):
    """Root endpoint."""
    return Response({"message": "hello world"})


@api_view(['GET'])
def is_alive(request):
    """Check if the runtime is alive."""
    return Response(serialize_model(runtime.is_alive()))


@api_view(['POST'])
def create_session(request):
    """Create a new session."""
    request_data = CreateSessionRequest(**request.data)
    return Response(serialize_model(runtime.create_session(request_data)))


@api_view(['POST'])
def run_in_session(request):
    """Run an action in a session."""
    action = Action(**request.data)
    return Response(serialize_model(runtime.run_in_session(action)))


@api_view(['POST'])
def close_session(request):
    """Close a session."""
    request_data = CloseSessionRequest(**request.data)
    return Response(serialize_model(runtime.close_session(request_data)))


@api_view(['POST'])
def execute(request):
    """Execute a command."""
    command = Command(**request.data)
    return Response(serialize_model(runtime.execute(command)))


@api_view(['POST'])
def read_file(request):
    """Read a file."""
    request_data = ReadFileRequest(**request.data)
    return Response(serialize_model(runtime.read_file(request_data)))


@api_view(['POST'])
def write_file(request):
    """Write to a file."""
    request_data = WriteFileRequest(**request.data)
    return Response(serialize_model(runtime.write_file(request_data)))


class UploadFileView(APIView):
    """View for file uploads."""
    parser_classes = [MultiPartParser]

    def post(self, request):
        """Handle file upload."""
        file = request.FILES.get('file')
        target_path = request.POST.get('target_path')
        unzip = request.POST.get('unzip', 'False').lower() == 'true'

        if not file or not target_path:
            return Response(
                {"error": "Both file and target_path are required"}, 
                status=400
            )

        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "temp_file_transfer"
            with open(file_path, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)

            if unzip:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(target_path)
                file_path.unlink()
            else:
                shutil.move(file_path, target_path)

        return Response(UploadResponse().model_dump())


@api_view(['POST'])
def close(request):
    """Close the runtime."""
    runtime.close()
    return Response(CloseResponse().model_dump())
