"""
Status hooks for Veigar security agent.

This module provides status hooks for the Veigar security agent.
"""

import logging
import time
from typing import Any, Dict, Optional

from backend.apps.agent.veigar.agent.hooks.abstract import AbstractHook

logger = logging.getLogger(__name__)

class StatusHook(AbstractHook):
    """Hook for tracking and reporting status."""
    
    def __init__(self):
        """Initialize the status hook."""
        super().__init__("status")
        self.start_time = None
        self.end_time = None
        self.error = None
    
    def before_run(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute before the agent runs.
        
        Args:
            context: Optional context for execution.
        """
        logger.info("Starting security agent run")
        self.start_time = time.time()
        self.end_time = None
        self.error = None
    
    def after_run(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute after the agent runs.
        
        Args:
            context: Optional context for execution.
        """
        self.end_time = time.time()
        if self.start_time is not None:
            duration = self.end_time - self.start_time
            logger.info(f"Security agent run completed in {duration:.2f} seconds")
        else:
            logger.info("Security agent run completed")
        
        if context and "result" in context:
            logger.info(f"Security agent run result: {context['result']}")
    
    def on_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute when an error occurs.
        
        Args:
            error: The error that occurred.
            context: Optional context for execution.
        """
        self.error = error
        self.end_time = time.time()
        if self.start_time is not None:
            duration = self.end_time - self.start_time
            logger.error(f"Security agent run failed after {duration:.2f} seconds: {error}")
        else:
            logger.error(f"Security agent run failed: {error}")
