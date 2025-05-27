"""
Mock swerex runtime abstract module for local development.
"""

from typing import Dict, List, Any, Optional, Union


class Command:
    """Mock Command class for local development."""
    
    def __init__(self, command_type: str, args: Dict[str, Any] = None):
        """
        Initialize Command.
        
        Args:
            command_type: Type of command
            args: Command arguments
        """
        self.command_type = command_type
        self.args = args or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Command to dictionary.
        
        Returns:
            Dict[str, Any]: Command as dictionary
        """
        return {
            'command_type': self.command_type,
            'args': self.args
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """
        Create Command from dictionary.
        
        Args:
            data: Dictionary representation of Command
            
        Returns:
            Command: Command instance
        """
        return cls(
            command_type=data.get('command_type', ''),
            args=data.get('args', {})
        )


class UploadRequest:
    """Mock UploadRequest class for local development."""
    
    def __init__(self, file_path: str, content: str, metadata: Dict[str, Any] = None):
        """
        Initialize UploadRequest.
        
        Args:
            file_path: Path to file
            content: File content
            metadata: File metadata
        """
        self.file_path = file_path
        self.content = content
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert UploadRequest to dictionary.
        
        Returns:
            Dict[str, Any]: UploadRequest as dictionary
        """
        return {
            'file_path': self.file_path,
            'content': self.content,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadRequest':
        """
        Create UploadRequest from dictionary.
        
        Args:
            data: Dictionary representation of UploadRequest
            
        Returns:
            UploadRequest: UploadRequest instance
        """
        return cls(
            file_path=data.get('file_path', ''),
            content=data.get('content', ''),
            metadata=data.get('metadata', {})
        )
