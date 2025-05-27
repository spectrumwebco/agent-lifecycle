"""
Abstract run hooks for Veigar security agent.

This module provides abstract run hooks for the Veigar security agent.
"""

import abc
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class AbstractRunHook(abc.ABC):
    """Abstract base class for run hooks."""
    
    def __init__(self, name: str):
        """
        Initialize the run hook.
        
        Args:
            name: Name of the hook.
        """
        self.name = name
        logger.info(f"Initialized run hook: {name}")
    
    @abc.abstractmethod
    def before_review(self, code: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute before the security review.
        
        Args:
            code: Code to review.
            context: Optional context for execution.
        """
        pass
    
    @abc.abstractmethod
    def after_review(self, code: str, result: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute after the security review.
        
        Args:
            code: Code that was reviewed.
            result: Result of the security review.
            context: Optional context for execution.
        """
        pass
    
    @abc.abstractmethod
    def on_error(self, code: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute when an error occurs during the security review.
        
        Args:
            code: Code that was being reviewed.
            error: The error that occurred.
            context: Optional context for execution.
        """
        pass
