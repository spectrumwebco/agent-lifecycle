"""
Status environment hooks for Veigar security agent.

This module provides status environment hooks for the Veigar security agent.
"""

import logging
import os
import platform
import sys
from typing import Any, Dict, Optional

from backend.apps.agent.veigar.agent.environment.hooks.abstract import AbstractEnvironmentHook

logger = logging.getLogger(__name__)

class StatusEnvironmentHook(AbstractEnvironmentHook):
    """Environment hook for checking and reporting status."""
    
    def __init__(self):
        """Initialize the status environment hook."""
        super().__init__("status")
        self.status = {}
    
    def setup(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Set up the environment status.
        
        Args:
            context: Optional context for setup.
        """
        logger.info("Setting up status environment hook")
        
        self.status = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "hostname": platform.node(),
            "environment_variables": {
                key: value for key, value in os.environ.items()
                if key.startswith(("VEIGAR_", "AGENT_", "DJANGO_"))
            },
            "working_directory": os.getcwd(),
        }
        
        if context:
            self.status["context"] = context
        
        logger.info("Status environment hook setup complete")
    
    def teardown(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Tear down the environment status.
        
        Args:
            context: Optional context for teardown.
        """
        logger.info("Tearing down status environment hook")
        self.status = {}
        logger.info("Status environment hook teardown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the environment.
        
        Returns:
            The status of the environment.
        """
        return self.status
