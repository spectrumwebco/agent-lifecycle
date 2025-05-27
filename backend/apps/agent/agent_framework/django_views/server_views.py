"""
Django views to replace FastAPI server functionality.

This module provides Django views that replace the functionality
previously provided by the FastAPI server in server.py.
"""

import json
import logging
import shutil
import tempfile
import traceback
import zipfile
from pathlib import Path

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

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

logger = logging.getLogger(__name__)
runtime = LocalRuntime()


def serialize_model(model):
    """Serialize a Pydantic model to a dictionary."""
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def root(request):
    """Root endpoint."""
    return Response({"message": "hello world"})


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def is_alive(request):
    """Check if the runtime is alive."""
    try:
        result = runtime.is_alive()
        return Response(serialize_model(result))
    except Exception as e:
        logger.error(f"Error in is_alive: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_session(request):
    """Create a new session."""
    try:
        session_request = CreateSessionRequest(**request.data)
        result = runtime.create_session(session_request)
        return Response(serialize_model(result))
    except Exception as e:
        logger.error(f"Error in create_session: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def run_in_session(request):
    """Run an action in a session."""
    try:
        action = Action(**request.data)
        result = runtime.run_in_session(action)
        return Response(serialize_model(result))
    except Exception as e:
        logger.error(f"Error in run_in_session: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def close_session(request):
    """Close a session."""
    try:
        close_request = CloseSessionRequest(**request.data)
        result = runtime.close_session(close_request)
        return Response(serialize_model(result))
    except Exception as e:
        logger.error(f"Error in close_session: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def execute(request):
    """Execute a command."""
    try:
        command = Command(**request.data)
        result = runtime.execute(command)
        return Response(serialize_model(result))
    except Exception as e:
        logger.error(f"Error in execute: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def read_file(request):
    """Read a file."""
    try:
        read_request = ReadFileRequest(**request.data)
        result = runtime.read_file(read_request)
        return Response(serialize_model(result))
    except Exception as e:
        logger.error(f"Error in read_file: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def write_file(request):
    """Write a file."""
    try:
        write_request = WriteFileRequest(**request.data)
        result = runtime.write_file(write_request)
        return Response(serialize_model(result))
    except Exception as e:
        logger.error(f"Error in write_file: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def upload(request):
    """Upload a file."""
    try:
        file = request.FILES.get('file')
        target_path = request.POST.get('target_path')
        unzip = request.POST.get('unzip', 'False').lower() == 'true'
        
        if not file or not target_path:
            return Response(
                {"error": "Missing file or target_path"},
                status=status.HTTP_400_BAD_REQUEST
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
        
        return Response(UploadResponse().dict())
    except Exception as e:
        logger.error(f"Error in upload: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def close(request):
    """Close the runtime."""
    try:
        runtime.close()
        return Response(CloseResponse().dict())
    except Exception as e:
        logger.error(f"Error in close: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def version(request):
    """Get the version of the agent framework."""
    return Response({"version": __version__})
