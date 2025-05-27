"""
Tests for the Veigar static analysis tool.

This module contains tests for the static analysis tool component of the Veigar agent.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import random

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from veigar.tools.static_analysis import StaticAnalysisTool


class TestStaticAnalysisTool:
    """Test suite for the StaticAnalysisTool class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.analyzer = StaticAnalysisTool()
        self.test_files = [
            "/path/to/test.py",
            "/path/to/test.js",
            "/path/to/test.go",
            "/path/to/test.java",
            "/path/to/test.cpp"
        ]
        self.test_repo = "test-repo"
        self.test_branch = "main"

    def test_initialization(self):
        """Test that the analyzer initializes correctly."""
        assert hasattr(self.analyzer, "analyze")
        assert hasattr(self.analyzer, "_initialize_tools")
        assert len(self.analyzer.tools) > 0

    def test_tools_initialization(self):
        """Test that the tools are initialized correctly."""
        tools = self.analyzer._initialize_tools()
        
        tool_names = [tool["name"] for tool in tools]
        assert "semgrep" in tool_names
        assert "bandit" in tool_names
        assert "gosec" in tool_names
        assert "eslint-security" in tool_names
        assert "cppcheck" in tool_names
        
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "languages" in tool
            assert "source" in tool
            assert "enabled" in tool

    def test_group_files_by_language(self):
        """Test grouping files by language."""
        files = [
            "/path/to/file.py",
            "/path/to/file.js",
            "/path/to/file.go",
            "/path/to/file.java",
            "/path/to/file.cpp",
            "/path/to/file.unknown"
        ]
        
        result = self.analyzer._group_files_by_language(files)
        
        assert "python" in result
        assert "javascript" in result
        assert "go" in result
        assert "java" in result
        assert "cpp" in result
        assert len(result["python"]) == 1
        assert len(result["javascript"]) == 1
        assert len(result["go"]) == 1
        assert len(result["java"]) == 1
        assert len(result["cpp"]) == 1
        assert "unknown" not in result  # Unknown extension should be ignored

    def test_get_tools_for_language(self):
        """Test getting tools for a specific language."""
        python_tools = self.analyzer._get_tools_for_language("python")
        python_tool_names = [tool["name"] for tool in python_tools]
        assert "bandit" in python_tool_names
        assert "semgrep" in python_tool_names
        
        go_tools = self.analyzer._get_tools_for_language("go")
        go_tool_names = [tool["name"] for tool in go_tools]
        assert "gosec" in go_tool_names
        
        unsupported_tools = self.analyzer._get_tools_for_language("brainfuck")
        assert len(unsupported_tools) == 0

    @patch.object(StaticAnalysisTool, "_run_tool")
    def test_analyze(self, mock_run_tool):
        """Test the analyze method."""
        mock_run_tool.return_value = [
            {
                "tool": "semgrep",
                "title": "SQL Injection",
                "description": "Potential SQL injection vulnerability detected",
                "severity": "high",
                "file": "/path/to/test.py",
                "line": "42",
                "code": "query = 'SELECT * FROM users WHERE id = ' + user_id"
            }
        ]
        
        results = self.analyzer.analyze(
            repository=self.test_repo,
            branch=self.test_branch,
            files=self.test_files
        )
        
        assert results["status"] == "success"
        assert results["repository"] == self.test_repo
        assert results["branch"] == self.test_branch
        assert "findings" in results
        assert len(results["findings"]) > 0
        assert "summary" in results
        assert results["summary"]["total_findings"] > 0
        
        assert mock_run_tool.call_count > 0

    @patch.object(StaticAnalysisTool, "_run_tool")
    def test_analyze_with_empty_files(self, mock_run_tool):
        """Test analyzing with empty file list."""
        results = self.analyzer.analyze(
            repository=self.test_repo,
            branch=self.test_branch,
            files=[]
        )
        
        assert results["status"] == "success"
        assert results["repository"] == self.test_repo
        assert results["branch"] == self.test_branch
        assert len(results["findings"]) == 0
        assert results["summary"]["total_findings"] == 0
        
        mock_run_tool.assert_not_called()

    @patch.object(StaticAnalysisTool, "_run_tool")
    def test_analyze_with_exception(self, mock_run_tool):
        """Test analyzing when an exception occurs."""
        mock_run_tool.side_effect = Exception("Test exception")
        
        results = self.analyzer.analyze(
            repository=self.test_repo,
            branch=self.test_branch,
            files=self.test_files
        )
        
        assert results["status"] == "success"  # Overall status should still be success
        assert "findings" in results
        assert any(finding.get("status") == "error" for finding in results["findings"])
        
        assert mock_run_tool.call_count > 0

    def test_deduplicate_findings(self):
        """Test deduplicating findings."""
        findings = [
            {
                "tool": "semgrep",
                "title": "SQL Injection",
                "file": "/path/to/file.py",
                "line": "42"
            },
            {
                "tool": "semgrep",
                "title": "SQL Injection",
                "file": "/path/to/file.py",
                "line": "42"
            },
            {
                "tool": "bandit",
                "title": "SQL Injection",
                "file": "/path/to/file.py",
                "line": "42"
            },
            {
                "tool": "semgrep",
                "title": "XSS",
                "file": "/path/to/file.py",
                "line": "42"
            }
        ]
        
        deduplicated = self.analyzer._deduplicate_findings(findings)
        
        assert len(deduplicated) == 3  # Should remove one duplicate

    def test_simulate_semgrep_findings(self):
        """Test simulating semgrep findings."""
        findings = self.analyzer._simulate_semgrep_findings(self.test_files)
        
        assert isinstance(findings, list)
        if findings:  # If any findings were generated
            for finding in findings:
                assert "title" in finding
                assert "description" in finding
                assert "severity" in finding
                assert "file" in finding
                assert "line" in finding
                assert "code" in finding

    def test_simulate_bandit_findings(self):
        """Test simulating bandit findings."""
        findings = self.analyzer._simulate_bandit_findings(["/path/to/file.py"])
        
        assert isinstance(findings, list)
        if findings:  # If any findings were generated
            for finding in findings:
                assert "title" in finding
                assert "description" in finding
                assert "severity" in finding
                assert "file" in finding
                assert "line" in finding
                assert "code" in finding

    def test_simulate_gosec_findings(self):
        """Test simulating gosec findings."""
        findings = self.analyzer._simulate_gosec_findings(["/path/to/file.go"])
        
        assert isinstance(findings, list)
        if findings:  # If any findings were generated
            for finding in findings:
                assert "title" in finding
                assert "description" in finding
                assert "severity" in finding
                assert "file" in finding
                assert "line" in finding
                assert "code" in finding
                assert "G" in finding["title"]  # Gosec findings start with G followed by a number

    def test_simulate_eslint_findings(self):
        """Test simulating eslint findings."""
        findings = self.analyzer._simulate_eslint_findings(["/path/to/file.js"])
        
        assert isinstance(findings, list)
        if findings:  # If any findings were generated
            for finding in findings:
                assert "title" in finding
                assert "description" in finding
                assert "severity" in finding
                assert "file" in finding
                assert "line" in finding
                assert "code" in finding

    def test_simulate_cppcheck_findings(self):
        """Test simulating cppcheck findings."""
        findings = self.analyzer._simulate_cppcheck_findings(["/path/to/file.cpp"])
        
        assert isinstance(findings, list)
        if findings:  # If any findings were generated
            for finding in findings:
                assert "title" in finding
                assert "description" in finding
                assert "severity" in finding
                assert "file" in finding
                assert "line" in finding
                assert "code" in finding

    def test_simulate_sonarqube_findings(self):
        """Test simulating sonarqube findings."""
        findings = self.analyzer._simulate_sonarqube_findings(self.test_files)
        
        assert isinstance(findings, list)
        if findings:  # If any findings were generated
            for finding in findings:
                assert "title" in finding
                assert "description" in finding
                assert "severity" in finding
                assert "file" in finding
                assert "line" in finding
                assert "code" in finding
                assert "S" in finding["title"]  # SonarQube findings start with S followed by a number

    def test_simulate_flawfinder_findings(self):
        """Test simulating flawfinder findings."""
        findings = self.analyzer._simulate_flawfinder_findings(["/path/to/file.cpp"])
        
        assert isinstance(findings, list)
        if findings:  # If any findings were generated
            for finding in findings:
                assert "title" in finding
                assert "description" in finding
                assert "severity" in finding
                assert "file" in finding
                assert "line" in finding
                assert "code" in finding

    def test_simulate_brakeman_findings(self):
        """Test simulating brakeman findings."""
        findings = self.analyzer._simulate_brakeman_findings(["/path/to/file.rb"])
        
        assert isinstance(findings, list)
        if findings:  # If any findings were generated
            for finding in findings:
                assert "title" in finding
                assert "description" in finding
                assert "severity" in finding
                assert "file" in finding
                assert "line" in finding
                assert "code" in finding
