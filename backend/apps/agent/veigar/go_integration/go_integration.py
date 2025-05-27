"""
Go integration for the Veigar cybersecurity agent.

This module provides Go integration for the Veigar agent, connecting
the security review system with the Go framework for PR vulnerability scanning.
"""

import logging
from typing import Any, Dict, Optional

from apps.agent.go_integration import get_go_runtime_integration

logger = logging.getLogger(__name__)


class VeigarGoIntegration:
    """Go integration for the Veigar security agent."""

    def __init__(self):
        """Initialize the Veigar Go integration."""
        self.go_runtime = get_go_runtime_integration()
        self.connected = False

    def connect(self) -> bool:
        """Connect to the Go runtime."""
        if not self.connected:
            self.connected = self.go_runtime.connect()
        return self.connected

    def disconnect(self) -> bool:
        """Disconnect from the Go runtime."""
        if self.connected:
            self.connected = not self.go_runtime.disconnect()
        return not self.connected

    def register_security_tools(self) -> bool:
        """Register security tools with the Go runtime."""
        import json
        import os
        from pathlib import Path
        
        if not self.connected:
            if not self.connect():
                logger.error("Failed to connect to Go runtime")
                return False
        
        try:
            config_path = Path(os.path.dirname(os.path.dirname(__file__))) / "config" / "veigar_tools.json"
            logger.info("Loading tools from %s", config_path)
            
            with open(config_path, 'r') as f:
                tools_config = json.load(f)
                tools = tools_config.get("tools", [])
            
            logger.info("Loaded %d tools from configuration", len(tools))
        except Exception as e:
            logger.error("Failed to load tools configuration: %s", e)
            return False
        
        legacy_tools = [
            {
                "name": "static_analysis",
                "description": "Perform static analysis on code to identify security vulnerabilities",
                "parameters": {
                    "files": {
                        "type": "array",
                        "description": "List of files to analyze"
                    },
                    "depth": {
                        "type": "string",
                        "description": "Depth of analysis (basic, standard, deep)",
                        "default": "standard"
                    }
                }
            },
            {
                "name": "vulnerability_scan",
                "description": "Scan code and dependencies for known vulnerabilities",
                "parameters": {
                    "files": {
                        "type": "array",
                        "description": "List of files to scan"
                    },
                    "depth": {
                        "type": "string",
                        "description": "Depth of scanning (basic, standard, deep)",
                        "default": "standard"
                    }
                }
            },
            {
                "name": "compliance_check",
                "description": "Check code compliance with security frameworks",
                "parameters": {
                    "files": {
                        "type": "array",
                        "description": "List of files to check"
                    },
                    "frameworks": {
                        "type": "array",
                        "description": "List of frameworks to check compliance against",
                        "default": ["e8", "nist", "owasp"]
                    }
                }
            },
            {
                "name": "security_review",
                "description": "Perform a comprehensive security review of a pull request",
                "parameters": {
                    "repository": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name"
                    },
                    "pr_id": {
                        "type": "string",
                        "description": "Pull request ID"
                    },
                    "files": {
                        "type": "array",
                        "description": "List of files to review"
                    }
                }
            }
        ]
        
        all_tools = tools + legacy_tools
        logger.info("Registering %d tools with Go runtime", len(all_tools))
        
        for tool in all_tools:
            try:
                self.go_runtime.publish_event(
                    event_type="tool_registered",
                    data={
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                        "module": tool.get("module", ""),
                        "class": tool.get("class", "")
                    },
                    source="veigar",
                    metadata={}
                )
                logger.info("Registered tool: %s", tool['name'])
            except Exception as e:
                logger.error("Failed to register tool %s: %s", tool['name'], e)
                return False
        
        return True

    def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a tool call from the Go runtime.

        Args:
            tool_name: Name of the tool to call
            parameters: Parameters for the tool call

        Returns:
            Dict: The tool call result
        """
        logger.info("Handling tool call: %s with parameters: %s", tool_name, parameters)

        if tool_name == "static_analysis":
            from apps.agent.veigar.tools.static_analysis import StaticAnalysisTool

            files = parameters.get("files", [])
            depth = parameters.get("depth", "standard")

            tool = StaticAnalysisTool()
            result = tool.analyze(repository="", branch="", files=files)

            return {
                "status": "success",
                "findings": result.get("findings", []),
                "summary": result.get("summary", {})
            }

        elif tool_name == "vulnerability_scan":
            from apps.agent.veigar.tools.vulnerability_scanner import VulnerabilityScanner

            files = parameters.get("files", [])
            depth = parameters.get("depth", "standard")

            scanner = VulnerabilityScanner()
            result = scanner.scan(repository="", branch="", files=files)

            return {
                "status": "success",
                "vulnerabilities": result.get("vulnerabilities", []),
                "summary": result.get("summary", {})
            }

        elif tool_name == "compliance_check":
            from apps.agent.veigar.tools.compliance_checker import ComplianceChecker

            files = parameters.get("files", [])
            frameworks = parameters.get("frameworks", ["e8", "nist", "owasp"])

            checker = ComplianceChecker(frameworks)
            result = checker.check(repository="", branch="", files=files)

            return {
                "status": "success",
                "frameworks": result.get("frameworks", {}),
                "summary": result.get("summary", {})
            }

        elif tool_name == "security_review":
            from apps.agent.veigar.agent.security_reviewer import SecurityReviewer
            from apps.agent.veigar.django_integration.django_integration import (
                load_security_config
            )

            repository = parameters.get("repository", "")
            branch = parameters.get("branch", "")
            pr_id = parameters.get("pr_id", "")
            files = parameters.get("files", [])

            config = load_security_config()
            reviewer = SecurityReviewer.from_config(config)

            pr_data = {
                "repository": repository,
                "branch": branch,
                "pr_id": pr_id,
                "files": files
            }

            result = reviewer.review_pr(pr_data)

            return {
                "status": "success",
                "security_report": result.info.get("security_report", ""),
                "vulnerabilities": result.info.get("vulnerabilities", []),
                "compliance": result.info.get("compliance", {}),
                "severity_level": result.info.get("severity_level", "none")
            }

        else:
            logger.error("Unknown tool: %s", tool_name)
            return {
                "status": "error",
                "message": f"Unknown tool: {tool_name}"
            }

    def publish_security_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish a security event to the Go runtime.

        Args:
            event_type: Type of the event
            data: Event data
            metadata: Event metadata

        Returns:
            bool: Whether the event was published successfully
        """
        if not self.connected:
            if not self.connect():
                logger.error("Failed to connect to Go runtime")
                return False

        try:
            self.go_runtime.publish_event(
                event_type=event_type,
                data=data,
                source="veigar",
                metadata=metadata or {}
            )
            logger.info("Published security event: %s", event_type)
            return True
        except Exception as e:
            logger.error("Failed to publish security event: %s", e)
            return False


def get_veigar_go_integration() -> VeigarGoIntegration:
    """
    Get the Veigar Go integration instance.

    Returns:
        VeigarGoIntegration: The Veigar Go integration instance
    """
    return VeigarGoIntegration()
