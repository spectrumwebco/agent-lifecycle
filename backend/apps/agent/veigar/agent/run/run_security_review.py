"""
Security review runner for Veigar security agent.

This module provides the security review runner for the Veigar security agent.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from backend.apps.agent.veigar.agent.hooks.status import StatusHook
from backend.apps.agent.veigar.agent.run.hooks.security_review import SecurityReviewHook
from backend.apps.agent.veigar.security.analyzer import SecurityAnalyzer
from backend.apps.agent.veigar.tools.common.utils import format_security_report

logger = logging.getLogger(__name__)

def run_security_review(code: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Run a security review on the provided code.
    
    Args:
        code: Code to review for security issues.
        context: Optional context for the security review.
        
    Returns:
        The security review results as a formatted string.
    """
    if context is None:
        context = {}
    
    status_hook = StatusHook()
    security_review_hook = SecurityReviewHook()
    
    try:
        status_hook.before_run(context)
        security_review_hook.before_review(code, context)
        
        analyzer = SecurityAnalyzer()
        
        vulnerabilities = analyzer.analyze_code(code)
        
        result = format_security_report(vulnerabilities)
        
        security_review_hook.after_review(code, result, context)
        status_hook.after_run({**context, "result": result})
        
        return result
    except Exception as e:
        logger.exception("Error running security review")
        
        security_review_hook.on_error(code, e, context)
        status_hook.on_error(e, context)
        
        raise
