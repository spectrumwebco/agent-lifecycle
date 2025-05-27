"""
Abstract environment hooks for Veigar security agent.

This module provides abstract environment hooks for the Veigar security agent.
"""

import abc
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class AbstractEnvironmentHook(abc.ABC):
    """Abstract base class for environment hooks."""
    
    def __init__(self, name: str):
        """
        Initialize the environment hook.
        
        Args:
            name: Name of the hook.
        """
        self.name = name
        logger.info(f"Initialized environment hook: {name}")
    
    @abc.abstractmethod
    def setup(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Set up the environment.
        
        Args:
            context: Optional context for setup.
        """
        pass
    
    @abc.abstractmethod
    def teardown(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Tear down the environment.
        
        Args:
            context: Optional context for teardown.
        """
        pass
    
    @abc.abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the environment.
        
        Returns:
            The status of the environment.
        """
        pass
