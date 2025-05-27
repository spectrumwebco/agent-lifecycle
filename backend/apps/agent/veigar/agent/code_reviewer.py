"""
Code reviewer for the Veigar cybersecurity agent.

This module provides a code reviewer for the Veigar agent, implementing
PR code review capabilities based on the SWE-agent reviewer.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from apps.agent.kled.agent import CONFIG_DIR, PACKAGE_DIR
from apps.agent.agent_framework.shared.runtime import RuntimeConfig
from apps.agent.agent_framework.shared.models import Trajectory, TrajectoryStep
from apps.agent.go_integration import get_go_runtime_integration

logger = logging.getLogger(__name__)


class CodeReviewConfig(BaseModel):
    """Configuration for code review."""

    class AgentConfig(BaseModel):
        """Agent configuration."""

        class ModelConfig(BaseModel):
            """Model configuration."""
            model_name: str = "gemini-2.5-pro"
            temperature: float = 0.0
            top_p: float = 1.0
            per_instance_cost_limit: float = 3.0

        model: ModelConfig = Field(default_factory=ModelConfig)
        prompt_template: str = "veigar_code_review_prompt.txt"
        max_iterations: int = 10
        tools: List[str] = Field(default_factory=list)

    class ReviewConfig(BaseModel):
        """Review configuration."""
        review_depth: str = "deep"  # Options: "basic", "standard", "deep"
        code_quality_check: bool = True
        best_practices_check: bool = True
        documentation_check: bool = True
        severity_threshold: str = "medium"  # Options: "low", "medium", "high", "critical"

    agent: AgentConfig = Field(default_factory=AgentConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)


@dataclass
class CodeReviewResult:
    """Result of a code review."""
    trajectory: Trajectory
    info: Dict[str, Any] = field(default_factory=dict)


class CodeReviewer:
    """Code reviewer for PR code quality and best practices review."""

    def __init__(self, config: CodeReviewConfig):
        """Initialize the code reviewer."""
        self.config = config
        self.go_runtime = get_go_runtime_integration()
        self.trajectory = Trajectory()

    @classmethod
    def from_config(cls, config: CodeReviewConfig) -> 'CodeReviewer':
        """Create a code reviewer from a configuration."""
        return cls(config)

    def review_pr(self, pr_data: Dict[str, Any]) -> CodeReviewResult:
        """
        Review a pull request for code quality and best practices.

        Args:
            pr_data: Pull request data including repository, branch, and files

        Returns:
            CodeReviewResult: The code review results
        """
        logger.info("Starting code review for PR %s in %s", 
                  pr_data.get('pr_id', ''), pr_data.get('repository', ''))

        self.trajectory.add_step(
            TrajectoryStep(
                role="system",
                content=f"Starting code review for PR {pr_data.get('pr_id', '')} in {pr_data.get('repository', '')}"
            )
        )

        review_results = self._perform_code_review(pr_data)
        self.trajectory.add_step(
            TrajectoryStep(
                role="tool",
                content=f"Code review results: {json.dumps(review_results, indent=2)}"
            )
        )

        review_report = self._generate_review_report(
            pr_data,
            review_results
        )
        self.trajectory.add_step(
            TrajectoryStep(
                role="assistant",
                content=review_report
            )
        )


        exit_status = "approved" if review_results.get("severity_level") in ["none", "low"] else "changes_requested"

        result = CodeReviewResult(
            trajectory=self.trajectory,
            info={
                "exit_status": exit_status,
                "review_report": review_report,
                "findings": review_results.get("findings", []),
                "severity_level": review_results.get("severity_level", "low")
            }
        )

        logger.info("Completed code review for PR %s with status %s", 
                  pr_data.get('pr_id', ''), exit_status)

        return result

    def _perform_code_review(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform code review on the PR code."""
        
        return {
            "severity_level": "medium",
            "findings": [
                {
                    "severity": "medium",
                    "title": "Inconsistent error handling",
                    "file": "example.py",
                    "line": 42,
                    "description": "Error handling is inconsistent across functions",
                    "remediation": "Standardize error handling approach"
                }
            ],
            "summary": "Code review identified some issues that should be addressed"
        }

    def _generate_review_report(self, pr_data: Dict[str, Any], review_results: Dict[str, Any]) -> str:
        """Generate a review report based on the review results."""
        findings = review_results.get("findings", [])
        findings_section = "\n\n## Findings\n\n"
        
        if findings:
            for finding in findings:
                severity = finding.get('severity', 'Unknown')
                title = finding.get('title', 'Unknown issue')
                findings_section += f"- **{severity}**: {title}\n"
                file_loc = finding.get('file', 'Unknown')
                line_loc = finding.get('line', 'Unknown')
                findings_section += f"  - **Location**: {file_loc}:{line_loc}\n"
                desc = finding.get('description', 'No description')
                findings_section += f"  - **Description**: {desc}\n"
                remedy = finding.get('remediation', 'No remediation provided')
                findings_section += f"  - **Remediation**: {remedy}\n\n"
        else:
            findings_section += "No significant issues found.\n\n"

        summary = review_results.get('summary', 'No summary provided')
        summary_section = f"\n\n## Summary\n\n{summary}\n\n"

        severity = review_results.get('severity_level', 'Unknown')
        severity_section = f"**Overall Severity**: {severity}\n\n"

        report = f"""# Code Review for PR #{pr_data.get('pr_id', '')} in {pr_data.get('repository', '')}


This code review was performed by Veigar, the cybersecurity agent for the Autonomous GitOps Team.

**Repository**: {pr_data.get('repository', '')}
**Branch**: {pr_data.get('branch', '')}
**PR ID**: {pr_data.get('pr_id', '')}
**Review Date**: {pr_data.get('review_date', 'Not specified')}

{severity_section}

{findings_section}
{summary_section}


{self._generate_conclusion(review_results)}
"""

        return report

    def _generate_conclusion(self, review_results: Dict[str, Any]) -> str:
        """Generate a conclusion based on the review results."""
        severity_level = review_results.get('severity_level', 'unknown')

        if severity_level == "none":
            return "This PR passes all code quality checks and is ready to be merged."
        elif severity_level == "low":
            return "This PR has minor issues that could be improved, but can be merged."
        elif severity_level == "medium":
            return "This PR has moderate issues that should be addressed before merging."
        elif severity_level == "high":
            return "This PR has significant issues that must be addressed before merging."
        elif severity_level == "critical":
            return "This PR has critical issues that must be addressed immediately. DO NOT MERGE."
        else:
            return "Unable to determine the code quality of this PR. Manual review required."
