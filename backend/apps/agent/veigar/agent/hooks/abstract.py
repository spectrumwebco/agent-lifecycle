"""
Abstract hooks for Veigar security agent.

This module provides abstract hooks for the Veigar security agent.
"""

import abc
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class AbstractHook(abc.ABC):
    """Abstract base class for hooks."""
    
    def __init__(self, name: str):
        """
        Initialize the hook.
        
        Args:
            name: Name of the hook.
        """
        self.name = name
        logger.info(f"Initialized hook: {name}")
    
    @abc.abstractmethod
    def before_run(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute before the agent runs.
        
        Args:
            context: Optional context for execution.
        """
        pass
    
    @abc.abstractmethod
    def after_run(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute after the agent runs.
        
        Args:
            context: Optional context for execution.
        """
        pass
    
    @abc.abstractmethod
    def on_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute when an error occurs.
        
        Args:
            error: The error that occurred.
            context: Optional context for execution.
        """
        pass
