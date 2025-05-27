"""
Models for the Neovim API service.

This module defines the Pydantic models for the Neovim API service.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class NeovimStatus(str, Enum):
    """Status of a Neovim instance."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class NeovimInstance(BaseModel):
    """Neovim instance configuration."""
    id: str = Field(..., description="Unique identifier for the Neovim instance")
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional configuration for the Neovim instance"
    )


class NeovimCommand(BaseModel):
    """Command to execute in a Neovim instance."""
    id: str = Field(..., description="Neovim instance ID")
    command: str = Field(..., description="Command to execute")
    file: Optional[str] = Field(
        default=None,
        description="Optional file to open before executing the command"
    )


class NeovimBuffer(BaseModel):
    """Neovim buffer information."""
    id: int = Field(..., description="Buffer ID")
    file_path: Optional[str] = Field(
        default=None,
        description="Path to the file in the buffer"
    )
    modified: bool = Field(
        default=False,
        description="Whether the buffer has been modified"
    )


class NeovimWindow(BaseModel):
    """Neovim window information."""
    id: int = Field(..., description="Window ID")
    buffer_id: int = Field(..., description="ID of the buffer in the window")
    position: Dict[str, int] = Field(
        ...,
        description="Position of the window (row, column)"
    )
    size: Dict[str, int] = Field(
        ...,
        description="Size of the window (width, height)"
    )


class NeovimState(BaseModel):
    """State of a Neovim instance."""
    id: str = Field(..., description="Neovim instance ID")
    status: NeovimStatus = Field(
        ...,
        description="Status of the Neovim instance"
    )
    current_mode: str = Field(
        ...,
        description="Current mode (normal, insert, visual, etc.)"
    )
    current_file: Optional[str] = Field(
        default=None,
        description="Path to the current file"
    )
    cursor_position: Dict[str, int] = Field(
        ...,
        description="Cursor position (line, column)"
    )
    last_command: Optional[str] = Field(
        default=None,
        description="Last command executed"
    )
    command_history: List[str] = Field(
        default_factory=list,
        description="Command history"
    )
    buffers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of buffers"
    )
    windows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of windows"
    )
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp of the state"
    )


class NeovimResponse(BaseModel):
    """Response from the Neovim API."""
    status: str = Field(..., description="Status of the response (ok, error)")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Response data"
    )


class NeovimError(BaseModel):
    """Error response from the Neovim API."""
    status: str = Field(default="error", description="Error status")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )


class NeovimInstanceList(BaseModel):
    """List of Neovim instances."""
    instances: List[NeovimInstance] = Field(
        default_factory=list,
        description="List of Neovim instances"
    )


class NeovimBackgroundTask(BaseModel):
    """Background task in a Neovim instance."""
    id: str = Field(..., description="Task ID")
    instance_id: str = Field(..., description="Neovim instance ID")
    command: str = Field(..., description="Command being executed")
    status: str = Field(
        ...,
        description="Status of the task (running, completed, failed, cancelled)"
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Task result (if completed)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message (if failed)"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when the task was created"
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when the task was last updated"
    )
