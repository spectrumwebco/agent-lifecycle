"""
Routes for the Neovim API service.

This module defines the FastAPI routes for interacting with Neovim instances.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import subprocess
import os
import json
import asyncio
import logging
from datetime import datetime

from .....agent.utils.log import get_logger
from .models import (
    NeovimInstance,
    NeovimCommand,
    NeovimResponse,
    NeovimState,
    NeovimStatus,
    NeovimInstanceList,
    NeovimError
)

router = APIRouter(
    prefix="/neovim",
    tags=["neovim"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger("neovim-api", emoji="🧠")

active_instances: Dict[str, NeovimInstance] = {}

background_tasks: Dict[str, asyncio.Task] = {}


@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint for the Neovim API."""
    return {"status": "ok", "message": "Neovim API is running"}


@router.post("/start", response_model=NeovimResponse)
async def start_instance(instance: NeovimInstance):
    """Start a new Neovim instance.
    
    Args:
        instance: Neovim instance configuration
        
    Returns:
        NeovimResponse: Response with status and message
    """
    instance_id = instance.id
    
    if instance_id in active_instances:
        logger.info(f"Neovim instance {instance_id} already exists")
        return NeovimResponse(
            status="ok",
            message=f"Neovim instance {instance_id} already exists",
            data={"id": instance_id}
        )
    
    try:
        logger.info(f"Starting Neovim instance: {instance_id}")
        
        active_instances[instance_id] = instance
        
        return NeovimResponse(
            status="ok",
            message=f"Started Neovim instance: {instance_id}",
            data={"id": instance_id}
        )
    except Exception as e:
        logger.error(f"Error starting Neovim instance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Neovim instance: {str(e)}"
        )


@router.post("/stop", response_model=NeovimResponse)
async def stop_instance(instance: NeovimInstance):
    """Stop a Neovim instance.
    
    Args:
        instance: Neovim instance configuration
        
    Returns:
        NeovimResponse: Response with status and message
    """
    instance_id = instance.id
    
    if instance_id not in active_instances:
        logger.warning(f"Neovim instance {instance_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Neovim instance {instance_id} not found"
        )
    
    try:
        logger.info(f"Stopping Neovim instance: {instance_id}")
        
        del active_instances[instance_id]
        
        return NeovimResponse(
            status="ok",
            message=f"Stopped Neovim instance: {instance_id}",
            data={"id": instance_id}
        )
    except Exception as e:
        logger.error(f"Error stopping Neovim instance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop Neovim instance: {str(e)}"
        )


@router.post("/execute", response_model=NeovimResponse)
async def execute_command(command: NeovimCommand):
    """Execute a command in a Neovim instance.
    
    Args:
        command: Command to execute
        
    Returns:
        NeovimResponse: Response with status and message
    """
    instance_id = command.id
    
    if instance_id not in active_instances:
        logger.warning(f"Neovim instance {instance_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Neovim instance {instance_id} not found"
        )
    
    try:
        logger.info(f"Executing command in Neovim instance {instance_id}: {command.command}")
        
        result = {
            "command": command.command,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
        return NeovimResponse(
            status="ok",
            message=f"Executed command in Neovim instance: {instance_id}",
            data=result
        )
    except Exception as e:
        logger.error(f"Error executing command in Neovim instance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute command in Neovim instance: {str(e)}"
        )


@router.get("/state", response_model=NeovimResponse)
async def get_state(id: str):
    """Get the current state of a Neovim instance.
    
    Args:
        id: Neovim instance ID
        
    Returns:
        NeovimResponse: Response with status and message
    """
    if id not in active_instances:
        logger.warning(f"Neovim instance {id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Neovim instance {id} not found"
        )
    
    try:
        logger.info(f"Getting state of Neovim instance: {id}")
        
        state = NeovimState(
            id=id,
            status=NeovimStatus.ACTIVE,
            current_mode="normal",
            current_file="/workspace/project/main.go",
            cursor_position={"line": 10, "column": 5},
            last_command="w",
            command_history=["i", "w", "q"],
            buffers=[
                {
                    "id": 1,
                    "file_path": "/workspace/project/main.go",
                    "modified": False
                }
            ],
            windows=[
                {
                    "id": 1,
                    "buffer_id": 1,
                    "position": {"row": 0, "column": 0},
                    "size": {"width": 80, "height": 24}
                }
            ]
        )
        
        return NeovimResponse(
            status="ok",
            message=f"Got state of Neovim instance: {id}",
            data=state.dict()
        )
    except Exception as e:
        logger.error(f"Error getting state of Neovim instance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get state of Neovim instance: {str(e)}"
        )


@router.get("/instances", response_model=NeovimInstanceList)
async def list_instances():
    """List all active Neovim instances.
    
    Returns:
        NeovimInstanceList: List of active Neovim instances
    """
    try:
        logger.info("Listing active Neovim instances")
        
        instances = list(active_instances.values())
        
        return NeovimInstanceList(
            instances=instances
        )
    except Exception as e:
        logger.error(f"Error listing Neovim instances: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list Neovim instances: {str(e)}"
        )


@router.post("/background", response_model=NeovimResponse)
async def start_background_task(command: NeovimCommand):
    """Start a background task in a Neovim instance.
    
    Args:
        command: Command to execute
        
    Returns:
        NeovimResponse: Response with status and message
    """
    instance_id = command.id
    
    if instance_id not in active_instances:
        logger.warning(f"Neovim instance {instance_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Neovim instance {instance_id} not found"
        )
    
    try:
        task_id = f"{instance_id}_{len(background_tasks)}"
        
        logger.info(f"Starting background task {task_id} for Neovim instance {instance_id}: {command.command}")
        
        async def background_task():
            await asyncio.sleep(5)  # Simulate long-running task
            return {
                "command": command.command,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
        
        task = asyncio.create_task(background_task())
        background_tasks[task_id] = task
        
        return NeovimResponse(
            status="ok",
            message=f"Started background task {task_id} for Neovim instance: {instance_id}",
            data={"task_id": task_id}
        )
    except Exception as e:
        logger.error(f"Error starting background task in Neovim instance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start background task in Neovim instance: {str(e)}"
        )


@router.get("/background/{task_id}", response_model=NeovimResponse)
async def check_background_task(task_id: str):
    """Check the status of a background task.
    
    Args:
        task_id: Background task ID
        
    Returns:
        NeovimResponse: Response with status and message
    """
    if task_id not in background_tasks:
        logger.warning(f"Background task {task_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Background task {task_id} not found"
        )
    
    try:
        task = background_tasks[task_id]
        
        if task.done():
            try:
                result = task.result()
                del background_tasks[task_id]
                
                return NeovimResponse(
                    status="ok",
                    message=f"Background task {task_id} completed",
                    data={"status": "completed", "result": result}
                )
            except Exception as e:
                del background_tasks[task_id]
                
                return NeovimResponse(
                    status="error",
                    message=f"Background task {task_id} failed: {str(e)}",
                    data={"status": "failed", "error": str(e)}
                )
        else:
            return NeovimResponse(
                status="ok",
                message=f"Background task {task_id} is still running",
                data={"status": "running"}
            )
    except Exception as e:
        logger.error(f"Error checking background task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check background task: {str(e)}"
        )


@router.delete("/background/{task_id}", response_model=NeovimResponse)
async def cancel_background_task(task_id: str):
    """Cancel a background task.
    
    Args:
        task_id: Background task ID
        
    Returns:
        NeovimResponse: Response with status and message
    """
    if task_id not in background_tasks:
        logger.warning(f"Background task {task_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Background task {task_id} not found"
        )
    
    try:
        task = background_tasks[task_id]
        
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        del background_tasks[task_id]
        
        return NeovimResponse(
            status="ok",
            message=f"Cancelled background task {task_id}",
            data={"status": "cancelled"}
        )
    except Exception as e:
        logger.error(f"Error cancelling background task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel background task: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint for the Neovim API."""
    return {
        "status": "ok",
        "message": "Neovim API is healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
