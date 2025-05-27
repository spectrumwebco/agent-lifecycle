"""
Security analyzer for the Veigar cybersecurity agent.

This module provides security analysis capabilities for the Veigar agent,
analyzing security risks based on static analysis, vulnerability scanning,
and compliance checking results.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """Security analyzer for security risks."""
    
    def __init__(self, severity_threshold: str = "medium"):
        """
        Initialize the security analyzer.
        
        Args:
            severity_threshold: Minimum severity level to consider (low, medium, high, critical)
        """
        self.severity_threshold = severity_threshold
        self.severity_levels = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
            "info": 0,
            "none": 0
        }
        self.threshold_value = self.severity_levels.get(severity_threshold.lower(), 2)
        logger.info(f"Initialized security analyzer with severity threshold: {severity_threshold}")
    
    def analyze(
        self,
        static_analysis: Dict[str, Any],
        vulnerabilities: Dict[str, Any],
        compliance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze security risks based on all results.
        
        Args:
            static_analysis: Static analysis results
            vulnerabilities: Vulnerability scan results
            compliance: Compliance check results
            
        Returns:
            Dict: Security analysis results
        """
        logger.info("Analyzing security risks based on all results")
        
        static_findings = static_analysis.get("findings", [])
        
        vuln_findings = vulnerabilities.get("vulnerabilities", [])
        
        compliance_issues = []
        for framework, results in compliance.get("frameworks", {}).items():
            if isinstance(results, dict) and "issues" in results:
                for issue in results.get("issues", []):
                    issue["framework"] = framework
                    compliance_issues.append(issue)
        
        severity_level = self._determine_severity_level(
            static_findings, vuln_findings, compliance_issues
        )
        
        recommendations = self._generate_recommendations(
            static_findings, vuln_findings, compliance_issues, severity_level
        )
        
        summary = self._generate_summary(
            static_findings, vuln_findings, compliance_issues, severity_level
        )
        
        return {
            "status": "success",
            "severity_level": severity_level,
            "summary": summary,
            "recommendations": recommendations,
            "static_analysis_count": len(static_findings),
            "vulnerabilities_count": len(vuln_findings),
            "compliance_issues_count": len(compliance_issues),
            "total_issues": len(static_findings) + len(vuln_findings) + len(compliance_issues)
        }
    
    def _determine_severity_level(
        self,
        static_findings: List[Dict[str, Any]],
        vulnerabilities: List[Dict[str, Any]],
        compliance_issues: List[Dict[str, Any]]
    ) -> str:
        """Determine the overall severity level based on all findings."""
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for finding in static_findings:
            severity = finding.get("severity", "").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        for issue in compliance_issues:
            severity = issue.get("severity", "").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        if severity_counts["critical"] > 0:
            return "critical"
        elif severity_counts["high"] > 0:
            return "high"
        elif severity_counts["medium"] > 0:
            return "medium"
        elif severity_counts["low"] > 0:
            return "low"
        else:
            return "none"
    
    def _generate_recommendations(
        self,
        static_findings: List[Dict[str, Any]],
        vulnerabilities: List[Dict[str, Any]],
        compliance_issues: List[Dict[str, Any]],
        severity_level: str
    ) -> List[str]:
        """Generate recommendations based on all findings."""
        recommendations = []
        
        critical_high_findings = [
            f for f in static_findings 
            if f.get("severity", "").lower() in ["critical", "high"]
        ]
        critical_high_vulns = [
            v for v in vulnerabilities 
            if v.get("severity", "").lower() in ["critical", "high"]
        ]
        critical_high_issues = [
            i for i in compliance_issues 
            if i.get("severity", "").lower() in ["critical", "high"]
        ]
        
        for finding in critical_high_findings:
            if "remediation" in finding:
                recommendations.append(
                    f"Fix {finding.get('title', 'static analysis issue')}: {finding.get('remediation')}"
                )
        
        for vuln in critical_high_vulns:
            if "remediation" in vuln:
                recommendations.append(
                    f"Fix {vuln.get('title', 'vulnerability')}: {vuln.get('remediation')}"
                )
        
        for issue in critical_high_issues:
            if "remediation" in issue:
                framework = issue.get("framework", "").upper()
                recommendations.append(
                    f"Fix {framework} compliance issue - {issue.get('title', 'compliance issue')}: {issue.get('remediation')}"
                )
        
        if severity_level == "critical":
            recommendations.append("Immediately address all critical security issues before merging")
            recommendations.append("Conduct a comprehensive security review of the entire codebase")
        elif severity_level == "high":
            recommendations.append("Address all high severity security issues before merging")
            recommendations.append("Conduct a security review of affected components")
        elif severity_level == "medium":
            recommendations.append("Address medium severity security issues before merging if possible")
            recommendations.append("Create tickets for any issues that cannot be addressed immediately")
        elif severity_level == "low":
            recommendations.append("Create tickets to address low severity security issues in future sprints")
        
        unique_recommendations = list(set(recommendations))
        
        return unique_recommendations
    
    def _generate_summary(
        self,
        static_findings: List[Dict[str, Any]],
        vulnerabilities: List[Dict[str, Any]],
        compliance_issues: List[Dict[str, Any]],
        severity_level: str
    ) -> str:
        """Generate a summary based on all findings."""
        total_issues = len(static_findings) + len(vulnerabilities) + len(compliance_issues)
        
        if total_issues == 0:
            return "No security issues found. The code appears to be secure."
        
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for finding in static_findings + vulnerabilities + compliance_issues:
            severity = finding.get("severity", "").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        summary = f"Found {total_issues} security issues: "
        summary += f"{severity_counts['critical']} critical, "
        summary += f"{severity_counts['high']} high, "
        summary += f"{severity_counts['medium']} medium, "
        summary += f"{severity_counts['low']} low, "
        summary += f"{severity_counts['info']} info. "
        
        if severity_level == "critical":
            summary += "Critical security issues must be addressed before merging."
        elif severity_level == "high":
            summary += "High severity security issues should be addressed before merging."
        elif severity_level == "medium":
            summary += "Medium severity security issues should be addressed if possible."
        elif severity_level == "low":
            summary += "Low severity security issues can be addressed in future updates."
        else:
            summary += "No significant security issues found."
        
        return summary
