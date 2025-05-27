"""
Static analysis tool for the Veigar cybersecurity agent.

This module provides static code analysis capabilities for the Veigar agent,
integrating tools from various cybersecurity repositories.
"""

import os
import logging
import random
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class StaticAnalysisTool:
    """Static code analysis tool for security vulnerabilities."""

    def __init__(self):
        """Initialize the static analysis tool."""
        self.tools = self._initialize_tools()
        logger.info("Initialized static analysis tool with %d analyzers", len(self.tools))

    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize the static analysis tools."""
        return [
            {
                "name": "semgrep",
                "description": "Lightweight static analysis for many languages",
                "languages": ["python", "javascript", "go", "java", "c", "cpp"],
                "source": "awesome-static-analysis",
                "enabled": True
            },
            {
                "name": "bandit",
                "description": "Security oriented static analyzer for Python code",
                "languages": ["python"],
                "source": "awesome-static-analysis",
                "enabled": True
            },
            {
                "name": "gosec",
                "description": "Go security checker",
                "languages": ["go"],
                "source": "awesome-static-analysis",
                "enabled": True
            },
            {
                "name": "eslint-security",
                "description": "ESLint plugin for security linting in JavaScript",
                "languages": ["javascript"],
                "source": "awesome-static-analysis",
                "enabled": True
            },
            {
                "name": "cppcheck",
                "description": "Static analysis tool for C/C++ code",
                "languages": ["c", "cpp"],
                "source": "awesome-static-analysis",
                "enabled": True
            },
            {
                "name": "sonarqube",
                "description": "Continuous code quality and security platform",
                "languages": ["python", "javascript", "go", "java", "c", "cpp"],
                "source": "awesome-static-analysis",
                "enabled": True
            },
            {
                "name": "flawfinder",
                "description": "Examines C/C++ source code for security flaws",
                "languages": ["c", "cpp"],
                "source": "awesome-static-analysis",
                "enabled": True
            },
            {
                "name": "brakeman",
                "description": "Static analysis security vulnerability scanner for Ruby on Rails",
                "languages": ["ruby"],
                "source": "awesome-static-analysis",
                "enabled": True
            }
        ]

    def analyze(self, repository: str, branch: str, files: List[str]) -> Dict[str, Any]:
        """
        Perform static analysis on the specified files.

        Args:
            repository: Repository name
            branch: Branch name
            files: List of files to analyze

        Returns:
            Dict: Static analysis results
        """
        logger.info("Performing static analysis on %d files in %s:%s", len(files), repository, branch)

        files_by_language = self._group_files_by_language(files)

        results = {
            "status": "success",
            "repository": repository,
            "branch": branch,
            "findings": []
        }

        for language, language_files in files_by_language.items():
            language_tools = self._get_tools_for_language(language)

            if not language_tools:
                logger.warning("No static analysis tools available for %s", language)
                continue

            for tool in language_tools:
                try:
                    tool_results = self._run_tool(tool, language_files, repository, branch)
                    results["findings"].extend(tool_results)
                except Exception as e:
                    logger.error("Error running %s: %s", tool['name'], e)
                    results["findings"].append({
                        "tool": tool["name"],
                        "status": "error",
                        "error": str(e)
                    })

        results["findings"] = self._deduplicate_findings(results["findings"])

        results["summary"] = {
            "total_findings": len(results["findings"]),
            "critical": len([f for f in results["findings"] if f.get("severity") == "critical"]),
            "high": len([f for f in results["findings"] if f.get("severity") == "high"]),
            "medium": len([f for f in results["findings"] if f.get("severity") == "medium"]),
            "low": len([f for f in results["findings"] if f.get("severity") == "low"]),
            "info": len([f for f in results["findings"] if f.get("severity") == "info"])
        }

        logger.info("Static analysis complete with %d findings", 
                   results['summary']['total_findings'])

        return results

    def _group_files_by_language(self, files: List[str]) -> Dict[str, List[str]]:
        """Group files by language based on file extension."""
        extensions_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".swift": "swift",
            ".kt": "kotlin",
            ".rs": "rust"
        }

        files_by_language = {}

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            language = extensions_map.get(ext)

            if language:
                if language not in files_by_language:
                    files_by_language[language] = []
                files_by_language[language].append(file)

        return files_by_language

    def _get_tools_for_language(self, language: str) -> List[Dict[str, Any]]:
        """Get tools that support the specified language."""
        return [
            tool for tool in self.tools
            if tool["enabled"] and language in tool["languages"]
        ]

    def _run_tool(
        self,
        tool: Dict[str, Any],
        files: List[str],
        repository: str,
        branch: str
    ) -> List[Dict[str, Any]]:
        """
        Run a static analysis tool on the specified files.

        In a real implementation, this would execute the actual tool.
        For now, we'll simulate tool execution with realistic findings.
        """
        tool_name = tool["name"]
        findings = []

        if tool_name == "semgrep":
            findings = self._simulate_semgrep_findings(files)
        elif tool_name == "bandit":
            findings = self._simulate_bandit_findings(files)
        elif tool_name == "gosec":
            findings = self._simulate_gosec_findings(files)
        elif tool_name == "eslint-security":
            findings = self._simulate_eslint_findings(files)
        elif tool_name == "cppcheck":
            findings = self._simulate_cppcheck_findings(files)
        elif tool_name == "sonarqube":
            findings = self._simulate_sonarqube_findings(files)
        elif tool_name == "flawfinder":
            findings = self._simulate_flawfinder_findings(files)
        elif tool_name == "brakeman":
            findings = self._simulate_brakeman_findings(files)

        for finding in findings:
            finding["tool"] = tool_name
            finding["source"] = tool["source"]

        return findings

    def _simulate_semgrep_findings(self, files: List[str]) -> List[Dict[str, Any]]:
        """Simulate semgrep findings."""
        findings = []

        issues = [
            {
                "title": "SQL Injection",
                "description": "Potential SQL injection vulnerability detected",
                "severity": "high",
                "cwe": "CWE-89",
                "remediation": "Use parameterized queries or prepared statements"
            },
            {
                "title": "Cross-Site Scripting (XSS)",
                "description": "Potential XSS vulnerability detected",
                "severity": "high",
                "cwe": "CWE-79",
                "remediation": "Use context-specific output encoding"
            },
            {
                "title": "Hardcoded Credentials",
                "description": "Hardcoded credentials detected",
                "severity": "critical",
                "cwe": "CWE-798",
                "remediation": "Use environment variables or a secure credential store"
            },
            {
                "title": "Insecure Deserialization",
                "description": "Potential insecure deserialization vulnerability",
                "severity": "high",
                "cwe": "CWE-502",
                "remediation": "Validate and sanitize input before deserialization"
            },
            {
                "title": "Command Injection",
                "description": "Potential command injection vulnerability",
                "severity": "high",
                "cwe": "CWE-78",
                "remediation": "Use safe APIs or properly escape inputs"
            }
        ]

        for file in random.sample(files, min(len(files), 3)):
            for _ in range(random.randint(0, 2)):
                issue = random.choice(issues)
                finding = issue.copy()
                finding["file"] = file
                finding["line"] = str(random.randint(10, 500))
                finding["code"] = f"Example vulnerable code in {file}"
                findings.append(finding)

        return findings

    def _simulate_bandit_findings(self, files: List[str]) -> List[Dict[str, Any]]:
        """Simulate bandit findings for Python files."""
        findings = []

        issues = [
            {
                "title": "Use of insecure MD5 hash function",
                "description": "MD5 is a cryptographically broken hash function",
                "severity": "medium",
                "cwe": "CWE-327",
                "remediation": "Use a secure hashing function like SHA-256"
            },
            {
                "title": "Use of eval()",
                "description": "Use of eval() is insecure",
                "severity": "high",
                "cwe": "CWE-95",
                "remediation": "Avoid using eval() with untrusted input"
            },
            {
                "title": "Possible shell injection",
                "description": "Possible shell injection via subprocess call",
                "severity": "high",
                "cwe": "CWE-78",
                "remediation": "Use subprocess.run with shell=False"
            },
            {
                "title": "Possible SQL injection",
                "description": "SQL injection via string formatting",
                "severity": "high",
                "cwe": "CWE-89",
                "remediation": "Use parameterized queries"
            },
            {
                "title": "Weak cryptography",
                "description": "Use of weak cryptographic algorithm",
                "severity": "medium",
                "cwe": "CWE-326",
                "remediation": "Use strong cryptographic algorithms"
            }
        ]

        for file in random.sample(files, min(len(files), 2)):
            for _ in range(random.randint(0, 2)):
                issue = random.choice(issues)
                finding = issue.copy()
                finding["file"] = file
                finding["line"] = str(random.randint(10, 500))
                finding["code"] = f"Example vulnerable code in {file}"
                findings.append(finding)

        return findings

    def _simulate_gosec_findings(self, files: List[str]) -> List[Dict[str, Any]]:
        """Simulate gosec findings for Go files."""
        findings = []

        issues = [
            {
                "title": "G101: Hardcoded credentials",
                "description": "Hardcoded credentials detected in source code",
                "severity": "critical",
                "cwe": "CWE-798",
                "remediation": "Use environment variables or a secure credential store"
            },
            {
                "title": "G102: Bind to all interfaces",
                "description": "Binding to all network interfaces",
                "severity": "medium",
                "cwe": "CWE-200",
                "remediation": "Bind to specific interfaces instead of 0.0.0.0"
            },
            {
                "title": "G103: Unsafe use of unsafe package",
                "description": "Use of unsafe package without proper validation",
                "severity": "medium",
                "cwe": "CWE-119",
                "remediation": "Avoid using unsafe package or ensure proper bounds checking"
            },
            {
                "title": "G104: Unhandled errors",
                "description": "Errors not being handled",
                "severity": "medium",
                "cwe": "CWE-391",
                "remediation": "Implement proper error handling"
            },
            {
                "title": "G107: Insecure URL validation",
                "description": "URL not properly validated before request",
                "severity": "high",
                "cwe": "CWE-918",
                "remediation": "Implement proper URL validation to prevent SSRF"
            }
        ]

        for file in random.sample(files, min(len(files), 2)):
            for _ in range(random.randint(0, 2)):
                issue = random.choice(issues)
                finding = issue.copy()
                finding["file"] = file
                finding["line"] = str(random.randint(10, 500))
                finding["code"] = f"Example vulnerable Go code in {file}"
                findings.append(finding)

        return findings

    def _simulate_eslint_findings(self, files: List[str]) -> List[Dict[str, Any]]:
        """Simulate eslint-security findings for JavaScript files."""
        findings = []

        issues = [
            {
                "title": "no-eval: Use of eval()",
                "description": "Use of eval() is insecure",
                "severity": "high",
                "cwe": "CWE-95",
                "remediation": "Avoid using eval() with untrusted input"
            },
            {
                "title": "no-implied-eval: Use of implied eval",
                "description": "Use of functions like setTimeout with string arguments",
                "severity": "high",
                "cwe": "CWE-95",
                "remediation": "Use function references instead of strings"
            },
            {
                "title": "no-innerHTML: Use of innerHTML",
                "description": "Use of innerHTML can lead to XSS vulnerabilities",
                "severity": "high",
                "cwe": "CWE-79",
                "remediation": "Use textContent or DOM methods instead"
            },
            {
                "title": "detect-non-literal-regexp: Non-literal RegExp",
                "description": "Non-literal RegExp can lead to ReDoS attacks",
                "severity": "medium",
                "cwe": "CWE-400",
                "remediation": "Use literal RegExp patterns"
            },
            {
                "title": "detect-unsafe-regex: Unsafe RegExp",
                "description": "Potentially unsafe RegExp that could lead to ReDoS",
                "severity": "medium",
                "cwe": "CWE-400",
                "remediation": "Simplify RegExp patterns to avoid catastrophic backtracking"
            }
        ]

        for file in random.sample(files, min(len(files), 2)):
            for _ in range(random.randint(0, 2)):
                issue = random.choice(issues)
                finding = issue.copy()
                finding["file"] = file
                finding["line"] = str(random.randint(10, 500))
                finding["code"] = f"Example vulnerable JavaScript code in {file}"
                findings.append(finding)

        return findings

    def _simulate_cppcheck_findings(self, files: List[str]) -> List[Dict[str, Any]]:
        """Simulate cppcheck findings for C/C++ files."""
        findings = []

        issues = [
            {
                "title": "Buffer Overflow",
                "description": "Potential buffer overflow in array access",
                "severity": "high",
                "cwe": "CWE-120",
                "remediation": "Use bounds checking or safer alternatives like std::vector"
            },
            {
                "title": "Memory Leak",
                "description": "Memory allocated but not freed",
                "severity": "medium",
                "cwe": "CWE-401",
                "remediation": "Ensure all allocated memory is properly freed or use smart pointers"
            },
            {
                "title": "Uninitialized Variable",
                "description": "Variable used before initialization",
                "severity": "medium",
                "cwe": "CWE-457",
                "remediation": "Initialize all variables before use"
            },
            {
                "title": "Null Pointer Dereference",
                "description": "Potential null pointer dereference",
                "severity": "high",
                "cwe": "CWE-476",
                "remediation": "Check pointers for NULL before dereferencing"
            },
            {
                "title": "Integer Overflow",
                "description": "Potential integer overflow in calculation",
                "severity": "medium",
                "cwe": "CWE-190",
                "remediation": "Use appropriate integer types and check for overflow"
            }
        ]

        for file in random.sample(files, min(len(files), 2)):
            for _ in range(random.randint(0, 2)):
                issue = random.choice(issues)
                finding = issue.copy()
                finding["file"] = file
                finding["line"] = str(random.randint(10, 500))
                finding["code"] = f"Example vulnerable C/C++ code in {file}"
                findings.append(finding)

        return findings

    def _simulate_sonarqube_findings(self, files: List[str]) -> List[Dict[str, Any]]:
        """Simulate sonarqube findings."""
        findings = []

        issues = [
            {
                "title": "S1313: IP addresses should not be hardcoded",
                "description": "Hardcoded IP address detected",
                "severity": "medium",
                "cwe": "CWE-798",
                "remediation": "Use configuration files or environment variables for IP addresses"
            },
            {
                "title": "S2068: Credentials should not be hardcoded",
                "description": "Hardcoded credentials detected",
                "severity": "critical",
                "cwe": "CWE-798",
                "remediation": "Use a secure credential store or environment variables"
            },
            {
                "title": "S2076: OS commands should not be vulnerable to injection attacks",
                "description": "Potential command injection vulnerability",
                "severity": "high",
                "cwe": "CWE-78",
                "remediation": "Use safe APIs or properly escape inputs"
            },
            {
                "title": "S2631: Regular expressions should not be vulnerable to ReDoS",
                "description": "Regular expression vulnerable to ReDoS",
                "severity": "medium",
                "cwe": "CWE-400",
                "remediation": "Simplify regular expressions to avoid catastrophic backtracking"
            },
            {
                "title": "S5131: HTTP responses should not be vulnerable to XSS attacks",
                "description": "Potential XSS vulnerability in HTTP response",
                "severity": "high",
                "cwe": "CWE-79",
                "remediation": "Use context-specific output encoding"
            },
            {
                "title": "S5146: HTTP request redirections should not be open to forging attacks",
                "description": "Potential open redirect vulnerability",
                "severity": "medium",
                "cwe": "CWE-601",
                "remediation": "Validate redirect URLs against a whitelist"
            }
        ]

        for file in random.sample(files, min(len(files), 3)):
            for _ in range(random.randint(0, 2)):
                issue = random.choice(issues)
                finding = issue.copy()
                finding["file"] = file
                finding["line"] = str(random.randint(10, 500))
                finding["code"] = f"Example vulnerable code in {file}"
                findings.append(finding)

        return findings

    def _simulate_flawfinder_findings(self, files: List[str]) -> List[Dict[str, Any]]:
        """Simulate flawfinder findings for C/C++ files."""
        findings = []

        issues = [
            {
                "title": "strcpy: Does not check for buffer overflows",
                "description": "Use of strcpy without bounds checking",
                "severity": "high",
                "cwe": "CWE-120",
                "remediation": "Use strncpy or strlcpy instead"
            },
            {
                "title": "gets: Does not check for buffer overflows",
                "description": "Use of gets function which is deprecated",
                "severity": "critical",
                "cwe": "CWE-242",
                "remediation": "Use fgets instead"
            },
            {
                "title": "sprintf: Does not check for buffer overflows",
                "description": "Use of sprintf without bounds checking",
                "severity": "high",
                "cwe": "CWE-120",
                "remediation": "Use snprintf instead"
            },
            {
                "title": "system: Invokes a shell command processor",
                "description": "Use of system function which can lead to command injection",
                "severity": "high",
                "cwe": "CWE-78",
                "remediation": "Use execve or similar functions with proper argument validation"
            },
            {
                "title": "rand: Potentially predictable random numbers",
                "description": "Use of rand() which is not cryptographically secure",
                "severity": "medium",
                "cwe": "CWE-338",
                "remediation": "Use a cryptographically secure random number generator"
            }
        ]

        for file in random.sample(files, min(len(files), 2)):
            for _ in range(random.randint(0, 2)):
                issue = random.choice(issues)
                finding = issue.copy()
                finding["file"] = file
                finding["line"] = str(random.randint(10, 500))
                finding["code"] = f"Example vulnerable C/C++ code in {file}"
                findings.append(finding)

        return findings

    def _simulate_brakeman_findings(self, files: List[str]) -> List[Dict[str, Any]]:
        """Simulate brakeman findings for Ruby files."""
        findings = []

        issues = [
            {
                "title": "SQL Injection",
                "description": "Possible SQL injection vulnerability",
                "severity": "high",
                "cwe": "CWE-89",
                "remediation": "Use parameterized queries or ActiveRecord methods"
            },
            {
                "title": "Cross-Site Scripting",
                "description": "Possible XSS vulnerability",
                "severity": "high",
                "cwe": "CWE-79",
                "remediation": "Use Rails' built-in XSS protection like html_escape or sanitize"
            },
            {
                "title": "Mass Assignment",
                "description": "Unprotected mass assignment",
                "severity": "medium",
                "cwe": "CWE-915",
                "remediation": "Use strong_parameters or attr_accessible"
            },
            {
                "title": "Unsafe Redirect",
                "description": "Redirect to a user-supplied location",
                "severity": "medium",
                "cwe": "CWE-601",
                "remediation": "Validate redirect URLs against a whitelist"
            },
            {
                "title": "Command Injection",
                "description": "Possible command injection vulnerability",
                "severity": "high",
                "cwe": "CWE-78",
                "remediation": "Avoid system calls or use proper escaping"
            }
        ]

        for file in random.sample(files, min(len(files), 2)):
            for _ in range(random.randint(0, 2)):
                issue = random.choice(issues)
                finding = issue.copy()
                finding["file"] = file
                finding["line"] = str(random.randint(10, 500))
                finding["code"] = f"Example vulnerable Ruby code in {file}"
                findings.append(finding)

        return findings

    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate findings based on file, line, title, and tool."""
        unique_findings = {}

        for finding in findings:
            key = (
                finding.get("file", ""),
                finding.get("line", 0),
                finding.get("title", ""),
                finding.get("tool", "")  # Include tool in the deduplication key
            )

            if key not in unique_findings:
                unique_findings[key] = finding

        return list(unique_findings.values())
