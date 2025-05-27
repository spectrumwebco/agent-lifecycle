"""
Security review run hooks for Veigar security agent.

This module provides security review run hooks for the Veigar security agent.
"""

import logging
import time
from typing import Any, Dict, Optional

from backend.apps.agent.veigar.agent.run.hooks.abstract import AbstractRunHook

logger = logging.getLogger(__name__)

class SecurityReviewHook(AbstractRunHook):
    """Hook for security review operations."""
    
    def __init__(self):
        """Initialize the security review hook."""
        super().__init__("security_review")
        self.start_time = None
        self.end_time = None
        self.error = None
    
    def before_review(self, code: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute before the security review.
        
        Args:
            code: Code to review.
            context: Optional context for execution.
        """
        logger.info(f"Starting security review of code ({len(code)} characters)")
        self.start_time = time.time()
        self.end_time = None
        self.error = None
    
    def after_review(self, code: str, result: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute after the security review.
        
        Args:
            code: Code that was reviewed.
            result: Result of the security review.
            context: Optional context for execution.
        """
        self.end_time = time.time()
        if self.start_time is not None:
            duration = self.end_time - self.start_time
            logger.info(f"Security review completed in {duration:.2f} seconds")
        else:
            logger.info("Security review completed")
        
        logger.debug(f"Security review result: {result}")
    
    def on_error(self, code: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute when an error occurs during the security review.
        
        Args:
            code: Code that was being reviewed.
            error: The error that occurred.
            context: Optional context for execution.
        """
        self.error = error
        self.end_time = time.time()
        if self.start_time is not None:
            duration = self.end_time - self.start_time
            logger.error(f"Security review failed after {duration:.2f} seconds: {error}")
        else:
            logger.error(f"Security review failed: {error}")
