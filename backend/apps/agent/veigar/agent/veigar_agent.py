"""
Veigar agent implementation.

This module provides the main Veigar agent implementation that combines
security review and code review functionality.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from apps.agent.agent_framework.shared.models import Trajectory
from apps.agent.go_integration import get_go_runtime_integration

from apps.agent.veigar.agent.security_reviewer import SecurityReviewer, SecurityReviewConfig
from apps.agent.veigar.agent.code_reviewer import CodeReviewer, CodeReviewConfig
from apps.agent.veigar.tools.crypto import CryptoAnalyzer
from apps.agent.veigar.tools.pwn import VulnerabilityScanner, ExploitGenerator
from apps.agent.veigar.tools.rev import BinaryAnalyzer, DecompilerTool
from apps.agent.veigar.tools.web import WebVulnerabilityScanner
from apps.agent.veigar.tools.forensics import ForensicsAnalyzer
from apps.agent.veigar.tools.common import SecurityLogger, ReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class VeigarAgentResult:
    """Result of a Veigar agent run."""
    pr_id: str
    repository: str
    security_report: str = ""
    code_review_report: str = ""
    severity_level: str = "low"
    trajectory: Optional[Trajectory] = None
    info: Dict[str, Any] = field(default_factory=dict)


class VeigarAgent:
    """
    Veigar agent for PR security and code review.
    
    This agent combines security review and code review functionality
    to provide comprehensive PR analysis.
    """
    
    def __init__(self, security_config: SecurityReviewConfig, code_review_config: CodeReviewConfig):
        """Initialize the Veigar agent."""
        self.security_config = security_config
        self.code_review_config = code_review_config
        self.go_runtime = get_go_runtime_integration()
        
        self.security_reviewer = SecurityReviewer.from_config(security_config)
        self.code_reviewer = CodeReviewer.from_config(code_review_config)
        
    @classmethod
    def create_default(cls) -> 'VeigarAgent':
        """Create a Veigar agent with default configuration."""
        from apps.agent.veigar.django_integration.django_integration import load_security_config
        
        security_config = load_security_config()
        code_review_config = CodeReviewConfig()
        
        return cls(security_config, code_review_config)
    
    def review_pr(self, pr_data: Dict[str, Any]) -> VeigarAgentResult:
        """
        Perform a comprehensive review of a pull request.
        
        Args:
            pr_data: Pull request data including repository, branch, and files
            
        Returns:
            VeigarAgentResult: The combined review results
        """
        logger.info("Starting Veigar review for PR %s in %s", 
                  pr_data.get('pr_id', ''), pr_data.get('repository', ''))
        
        security_result = self.security_reviewer.review_pr(pr_data)
        
        code_review_result = self.code_reviewer.review_pr(pr_data)
        
        severity_levels = {
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        
        security_severity = security_result.info.get("severity_level", "low")
        code_review_severity = code_review_result.info.get("severity_level", "low")
        
        security_severity_value = severity_levels.get(security_severity, 1)
        code_review_severity_value = severity_levels.get(code_review_severity, 1)
        
        overall_severity_value = max(security_severity_value, code_review_severity_value)
        overall_severity = next(key for key, value in severity_levels.items() 
                             if value == overall_severity_value)
        
        result = VeigarAgentResult(
            pr_id=pr_data.get('pr_id', ''),
            repository=pr_data.get('repository', ''),
            security_report=security_result.info.get("security_report", ""),
            code_review_report=code_review_result.info.get("review_report", ""),
            severity_level=overall_severity,
            info={
                "security": security_result.info,
                "code_review": code_review_result.info,
                "overall_severity": overall_severity
            }
        )
        
        
        self.go_runtime.publish_event(
            event_type="veigar_review_completed",
            data={
                "pr_id": pr_data.get("pr_id", ""),
                "repository": pr_data.get("repository", ""),
                "branch": pr_data.get("branch", ""),
                "security_severity": security_severity,
                "code_review_severity": code_review_severity,
                "overall_severity": overall_severity
            },
            source="veigar",
            metadata={
                "security_vulnerabilities_count": len(security_result.info.get("vulnerabilities", [])),
                "code_findings_count": len(code_review_result.info.get("findings", []))
            }
        )
        
        logger.info("Completed Veigar review for PR %s with severity %s", 
                  pr_data.get('pr_id', ''), overall_severity)
        
        return result
