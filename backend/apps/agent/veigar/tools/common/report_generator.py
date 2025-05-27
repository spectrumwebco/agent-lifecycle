"""
Security report generation tools for Veigar.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates security reports from scan and analysis results.
    """
    
    def __init__(self, report_dir: str = "/tmp/veigar_reports"):
        """
        Initialize the report generator.
        
        Args:
            report_dir: Directory to store reports
        """
        self.report_dir = report_dir
        
        os.makedirs(report_dir, exist_ok=True)
    
    def generate_security_report(self, 
                               pr_data: Dict[str, Any], 
                               vulnerabilities: List[Dict[str, Any]],
                               compliance_results: Optional[Dict[str, Any]] = None,
                               static_analysis_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive security report.
        
        Args:
            pr_data: Pull request data
            vulnerabilities: List of detected vulnerabilities
            compliance_results: Compliance check results
            static_analysis_results: Static analysis results
            
        Returns:
            Dict containing the report data and metadata
        """
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        overall_severity = self._determine_overall_severity(severity_counts)
        
        report = {
            "report_id": f"veigar_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "pr_data": {
                "repository": pr_data.get("repository", ""),
                "branch": pr_data.get("branch", ""),
                "pr_id": pr_data.get("pr_id", ""),
                "author": pr_data.get("author", "")
            },
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "severity_counts": severity_counts,
                "overall_severity": overall_severity,
                "pass_status": overall_severity not in ["critical", "high"]
            },
            "vulnerabilities": vulnerabilities,
            "compliance": compliance_results or {},
            "static_analysis": static_analysis_results or {}
        }
        
        report_file = os.path.join(
            self.report_dir, 
            f"security_report_{pr_data.get('repository', 'unknown')}_{pr_data.get('pr_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        markdown_report = self._generate_markdown_report(report)
        markdown_file = report_file.replace(".json", ".md")
        
        with open(markdown_file, 'w') as f:
            f.write(markdown_report)
        
        return {
            "report": report,
            "report_file": report_file,
            "markdown_file": markdown_file
        }
    
    def _determine_overall_severity(self, severity_counts: Dict[str, int]) -> str:
        """Determine the overall severity based on vulnerability counts."""
        if severity_counts["critical"] > 0:
            return "critical"
        elif severity_counts["high"] > 0:
            return "high"
        elif severity_counts["medium"] > 0:
            return "medium"
        elif severity_counts["low"] > 0:
            return "low"
        else:
            return "info"
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate a markdown version of the security report."""
        markdown = f"# Security Report: {report['pr_data']['repository']} PR #{report['pr_data']['pr_id']}\n\n"
        
        markdown += "## Summary\n\n"
        markdown += f"- **Overall Severity**: {report['summary']['overall_severity'].upper()}\n"
        markdown += f"- **Pass Status**: {'PASS' if report['summary']['pass_status'] else 'FAIL'}\n"
        markdown += f"- **Total Vulnerabilities**: {report['summary']['total_vulnerabilities']}\n"
        markdown += "- **Vulnerability Counts**:\n"
        
        for severity, count in report['summary']['severity_counts'].items():
            markdown += f"  - {severity.capitalize()}: {count}\n"
        
        if report['vulnerabilities']:
            markdown += "\n## Vulnerabilities\n\n"
            
            severities = ["critical", "high", "medium", "low", "info"]
            
            for severity in severities:
                severity_vulns = [v for v in report['vulnerabilities'] if v.get('severity', '').lower() == severity]
                
                if severity_vulns:
                    markdown += f"### {severity.capitalize()} Severity\n\n"
                    
                    for i, vuln in enumerate(severity_vulns, 1):
                        markdown += f"#### {i}. {vuln.get('type', 'Unknown')}\n\n"
                        markdown += f"- **Description**: {vuln.get('description', 'No description')}\n"
                        
                        if 'file' in vuln:
                            markdown += f"- **File**: `{vuln['file']}`\n"
                        
                        if 'details' in vuln:
                            markdown += f"- **Details**: {vuln['details']}\n"
                        
                        markdown += "\n"
        
        if report['compliance']:
            markdown += "\n## Compliance Results\n\n"
            
            for framework, results in report['compliance'].items():
                markdown += f"### {framework}\n\n"
                markdown += f"- **Status**: {results.get('status', 'Unknown')}\n"
                
                if 'passed_checks' in results:
                    markdown += f"- **Passed Checks**: {len(results['passed_checks'])}\n"
                
                if 'failed_checks' in results:
                    markdown += f"- **Failed Checks**: {len(results['failed_checks'])}\n"
                    
                    if results['failed_checks']:
                        markdown += "\n#### Failed Checks\n\n"
                        
                        for check in results['failed_checks']:
                            markdown += f"- {check.get('name', 'Unknown')}: {check.get('description', 'No description')}\n"
                
                markdown += "\n"
        
        if report['static_analysis']:
            markdown += "\n## Static Analysis Results\n\n"
            markdown += f"- **Files Analyzed**: {report['static_analysis'].get('files_analyzed', 0)}\n"
            markdown += f"- **Issues Found**: {report['static_analysis'].get('issues_found', 0)}\n"
            
            if 'issues' in report['static_analysis'] and report['static_analysis']['issues']:
                markdown += "\n### Issues\n\n"
                
                for issue in report['static_analysis']['issues']:
                    markdown += f"- **{issue.get('type', 'Unknown')}**: {issue.get('description', 'No description')}"
                    
                    if 'file' in issue:
                        markdown += f" in `{issue['file']}`"
                    
                    if 'line' in issue:
                        markdown += f" at line {issue['line']}"
                    
                    markdown += "\n"
        
        markdown += f"\n\n---\n*Report generated by Veigar Security Agent on {report['timestamp']}*\n"
        
        return markdown
