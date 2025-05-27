"""
Security reviewer for the Veigar cybersecurity agent.

This module provides a security reviewer for the Veigar agent, implementing
PR vulnerability scanning and compliance checking with Defense for Australia E8 requirements.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from apps.agent.kled.agent import CONFIG_DIR, PACKAGE_DIR
from apps.agent.agent_framework.shared.runtime import RuntimeConfig
from apps.agent.agent_framework.shared.models import Trajectory, TrajectoryStep
from apps.agent.go_integration import get_go_runtime_integration

from apps.agent.veigar.tools.static_analysis import StaticAnalysisTool
from apps.agent.veigar.tools.vulnerability_scanner import VulnerabilityScanner as LegacyVulnerabilityScanner
from apps.agent.veigar.tools.compliance_checker import ComplianceChecker
from apps.agent.veigar.security.security_analyzer import SecurityAnalyzer

from apps.agent.veigar.tools.crypto import CryptoAnalyzer
from apps.agent.veigar.tools.pwn import VulnerabilityScanner, ExploitGenerator
from apps.agent.veigar.tools.rev import BinaryAnalyzer, DecompilerTool
from apps.agent.veigar.tools.web import WebVulnerabilityScanner
from apps.agent.veigar.tools.forensics import ForensicsAnalyzer
from apps.agent.veigar.tools.common import SecurityLogger, ReportGenerator

logger = logging.getLogger(__name__)


class SecurityReviewConfig(BaseModel):
    """Configuration for security review."""

    class AgentConfig(BaseModel):
        """Agent configuration."""

        class ModelConfig(BaseModel):
            """Model configuration."""
            model_name: str = "gemini-2.5-pro"
            temperature: float = 0.0
            top_p: float = 1.0
            per_instance_cost_limit: float = 3.0

        model: ModelConfig = Field(default_factory=ModelConfig)
        prompt_template: str = "veigar_security_prompt.txt"
        max_iterations: int = 10
        tools: List[str] = Field(default_factory=list)

    class SecurityConfig(BaseModel):
        """Security configuration."""
        compliance_frameworks: List[str] = Field(default_factory=lambda: ["e8", "nist", "owasp"])
        vulnerability_scan_depth: str = "deep"  # Options: "basic", "standard", "deep"
        static_analysis_enabled: bool = True
        dynamic_analysis_enabled: bool = False
        threat_intelligence_enabled: bool = True
        severity_threshold: str = "medium"  # Options: "low", "medium", "high", "critical"

    agent: AgentConfig = Field(default_factory=AgentConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


@dataclass
class SecurityReviewResult:
    """Result of a security review."""
    trajectory: Trajectory
    info: Dict[str, Any] = field(default_factory=dict)


class SecurityReviewer:
    """Security reviewer for PR vulnerability scanning."""

    def __init__(self, config: SecurityReviewConfig):
        """Initialize the security reviewer."""
        self.config = config
        self.go_runtime = get_go_runtime_integration()
        self.trajectory = Trajectory()

        self.static_analyzer = StaticAnalysisTool()
        self.vulnerability_scanner = VulnerabilityScanner()
        self.compliance_checker = ComplianceChecker(
            frameworks=self.config.security.compliance_frameworks
        )
        self.security_analyzer = SecurityAnalyzer(
            severity_threshold=self.config.security.severity_threshold
        )

        self.prompt_template = self._load_prompt_template()

    @classmethod
    def from_config(cls, config: SecurityReviewConfig) -> 'SecurityReviewer':
        """Create a security reviewer from a configuration."""
        return cls(config)

    def _load_prompt_template(self) -> str:
        """Load the prompt template."""
        try:
            prompt_path = Path(CONFIG_DIR) / self.config.agent.prompt_template
            if prompt_path.exists():
                return prompt_path.read_text()
            else:
                return """
                You are Veigar, a cybersecurity expert specializing in code security review.
                Your task is to review pull requests for security vulnerabilities and compliance issues.

                Focus on:
                1. Identifying security vulnerabilities in the code
                2. Checking compliance with Defense for Australia E8 requirements
                3. Providing detailed remediation recommendations

                Use the security tools available to you to perform a comprehensive security review.
                """
        except Exception as e:
            logger.error("Error loading prompt template: %s", e)
            return "You are Veigar, a cybersecurity expert specializing in code security review."

    def review_pr(self, pr_data: Dict[str, Any]) -> SecurityReviewResult:
        """
        Review a pull request for security vulnerabilities.

        Args:
            pr_data: Pull request data including repository, branch, and files

        Returns:
            SecurityReviewResult: The security review results
        """
        logger.info("Starting security review for PR %s in %s", 
                  pr_data.get('pr_id'), pr_data.get('repository'))

        self.trajectory.add_step(
            TrajectoryStep(
                role="system",
                content=f"Starting security review for PR {pr_data.get('pr_id')} in {pr_data.get('repository')}"
            )
        )

        if self.config.security.static_analysis_enabled:
            static_analysis_results = self._perform_static_analysis(pr_data)
            self.trajectory.add_step(
                TrajectoryStep(
                    role="tool",
                    content=f"Static analysis results: {json.dumps(static_analysis_results, indent=2)}"
                )
            )
        else:
            static_analysis_results = {"status": "skipped"}

        vulnerability_results = self._scan_vulnerabilities(pr_data)
        self.trajectory.add_step(
            TrajectoryStep(
                role="tool",
                content=f"Vulnerability scan results: {json.dumps(vulnerability_results, indent=2)}"
            )
        )

        compliance_results = self._check_compliance(pr_data)
        self.trajectory.add_step(
            TrajectoryStep(
                role="tool",
                content=f"Compliance check results: {json.dumps(compliance_results, indent=2)}"
            )
        )

        security_analysis = self._analyze_security(
            static_analysis_results,
            vulnerability_results,
            compliance_results
        )
        self.trajectory.add_step(
            TrajectoryStep(
                role="tool",
                content=f"Security analysis: {json.dumps(security_analysis, indent=2)}"
            )
        )

        security_report = self._generate_security_report(
            pr_data,
            static_analysis_results,
            vulnerability_results,
            compliance_results,
            security_analysis
        )
        self.trajectory.add_step(
            TrajectoryStep(
                role="assistant",
                content=security_report
            )
        )

        exit_status = "approved" if security_analysis.get("severity_level") in ["none", "low"] else "rejected"

        result = SecurityReviewResult(
            trajectory=self.trajectory,
            info={
                "exit_status": exit_status,
                "security_report": security_report,
                "vulnerabilities": vulnerability_results.get("vulnerabilities", []),
                "compliance": compliance_results,
                "severity_level": security_analysis.get("severity_level", "low")
            }
        )

        logger.info("Completed security review for PR %s with status %s", 
                  pr_data.get('pr_id'), exit_status)

        return result

    def _perform_static_analysis(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform static analysis on the PR code."""
        try:
            return self.static_analyzer.analyze(
                repository=pr_data.get("repository", ""),  # Set default empty string
                branch=pr_data.get("branch", ""),  # Set default empty string
                files=pr_data.get("files", [])
            )
        except Exception as e:
            logger.error("Error performing static analysis: %s", e)
            return {"status": "error", "error": str(e)}

    def _scan_vulnerabilities(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for vulnerabilities in the PR code."""
        try:
            return self.vulnerability_scanner.scan(
                repository=pr_data.get("repository", ""),  # Set default empty string
                branch=pr_data.get("branch", ""),  # Set default empty string
                files=pr_data.get("files", []),
                scan_depth=self.config.security.vulnerability_scan_depth
            )
        except Exception as e:
            logger.error("Error scanning vulnerabilities: %s", e)
            return {"status": "error", "error": str(e)}

    def _check_compliance(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with security frameworks."""
        try:
            return self.compliance_checker.check(
                repository=pr_data.get("repository", ""),  # Set default empty string
                branch=pr_data.get("branch", ""),  # Set default empty string
                files=pr_data.get("files", [])
            )
        except Exception as e:
            logger.error("Error checking compliance: %s", e)
            return {"status": "error", "error": str(e)}

    def _analyze_security(
        self,
        static_analysis_results: Dict[str, Any],
        vulnerability_results: Dict[str, Any],
        compliance_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze security risks based on all results."""
        try:
            return self.security_analyzer.analyze(
                static_analysis=static_analysis_results,
                vulnerabilities=vulnerability_results,
                compliance=compliance_results
            )
        except Exception as e:
            logger.error("Error analyzing security: %s", e)
            return {"status": "error", "error": str(e), "severity_level": "high"}

    def _generate_security_report(
        self,
        pr_data: Dict[str, Any],
        static_analysis_results: Dict[str, Any],
        vulnerability_results: Dict[str, Any],
        compliance_results: Dict[str, Any],
        security_analysis: Dict[str, Any]
    ) -> str:
        """Generate a security report based on all results."""
        vulnerabilities = vulnerability_results.get("vulnerabilities", [])
        vulnerability_section = "\n\n## Vulnerabilities\n\n"
        if vulnerabilities:
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'Unknown')
                title = vuln.get('title', 'Unknown vulnerability')
                vulnerability_section += f"- **{severity}**: {title}\n"
                file_loc = vuln.get('file', 'Unknown')
                line_loc = vuln.get('line', 'Unknown')
                vulnerability_section += f"  - **Location**: {file_loc}:{line_loc}\n"
                desc = vuln.get('description', 'No description')
                vulnerability_section += f"  - **Description**: {desc}\n"
                remedy = vuln.get('remediation', 'No remediation provided')
                vulnerability_section += f"  - **Remediation**: {remedy}\n\n"
        else:
            vulnerability_section += "No vulnerabilities found.\n\n"

        compliance_section = "\n\n## Compliance\n\n"
        for framework, results in compliance_results.items():
            if framework == "status" or framework == "error":
                continue

            compliance_section += f"### {framework.upper()}\n\n"
            issues = results.get("issues", [])
            if issues:
                for issue in issues:
                    severity = issue.get('severity', 'Unknown')
                    title = issue.get('title', 'Unknown issue')
                    compliance_section += f"- **{severity}**: {title}\n"
                    desc = issue.get('description', 'No description')
                    compliance_section += f"  - **Description**: {desc}\n"
                    remedy = issue.get('remediation', 'No remediation provided')
                    compliance_section += f"  - **Remediation**: {remedy}\n\n"
            else:
                compliance_section += f"Compliant with {framework.upper()} requirements.\n\n"

        analysis_section = "\n\n## Security Analysis\n\n"
        severity = security_analysis.get('severity_level', 'Unknown')
        analysis_section += f"**Overall Severity**: {severity}\n\n"
        summary = security_analysis.get('summary', 'No summary provided')
        analysis_section += f"**Summary**: {summary}\n\n"

        recommendations = security_analysis.get('recommendations', [])
        if recommendations:
            analysis_section += "**Recommendations**:\n\n"
            for rec in recommendations:
                analysis_section += f"- {rec}\n"

        report = f"""# Security Review for PR #{pr_data.get('pr_id')} in {pr_data.get('repository')}


This security review was performed by Veigar, the cybersecurity agent for the Autonomous GitOps Team.

**Repository**: {pr_data.get('repository')}
**Branch**: {pr_data.get('branch')}
**PR ID**: {pr_data.get('pr_id')}
**Review Date**: {pr_data.get('review_date', 'Not specified')}

**Overall Status**: {security_analysis.get('severity_level', 'Unknown').upper()}

{vulnerability_section}
{compliance_section}
{analysis_section}


{self._generate_conclusion(security_analysis)}
"""

        return report

    def _generate_conclusion(self, security_analysis: Dict[str, Any]) -> str:
        """Generate a conclusion based on the security analysis."""
        severity_level = security_analysis.get('severity_level', 'unknown')

        if severity_level == "none":
            return "This PR passes all security checks and is ready to be merged."
        elif severity_level == "low":
            return "This PR has minor security issues that should be addressed, but can be merged with caution."
        elif severity_level == "medium":
            return "This PR has moderate security issues that should be addressed before merging."
        elif severity_level == "high":
            return "This PR has significant security issues that must be addressed before merging."
        elif severity_level == "critical":
            return "This PR has critical security issues that must be addressed immediately. DO NOT MERGE."
        else:
            return "Unable to determine the security status of this PR. Manual review required."
