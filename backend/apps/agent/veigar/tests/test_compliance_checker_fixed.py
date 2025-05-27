"""
Tests for the Veigar compliance checker.

This module contains tests for the compliance checker component of the Veigar agent.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from veigar.tools.compliance_checker import ComplianceChecker


class TestComplianceChecker:
    """Test suite for the ComplianceChecker class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.checker = ComplianceChecker()
        self.test_files = [
            "/path/to/config.py",
            "/path/to/auth.py",
            "/path/to/data.py",
            "/path/to/network.py"
        ]

    def test_initialization(self):
        """Test that the checker initializes correctly."""
        assert hasattr(self.checker, "check")
        assert hasattr(self.checker, "_check_framework")
        assert hasattr(self.checker, "_generate_summary")
        assert isinstance(self.checker.frameworks, list)
        assert len(self.checker.frameworks) > 0
        assert isinstance(self.checker.compliance_rules, dict)
        assert len(self.checker.compliance_rules) > 0

    def test_initialization_with_custom_frameworks(self):
        """Test initialization with custom frameworks."""
        custom_frameworks = ["e8", "nist"]
        checker = ComplianceChecker(frameworks=custom_frameworks)
        
        assert checker.frameworks == custom_frameworks
        assert isinstance(checker.compliance_rules, dict)
        assert len(checker.compliance_rules) > 0
        assert all(framework in checker.compliance_rules for framework in custom_frameworks)

    def test_load_e8_rules(self):
        """Test loading E8 compliance rules."""
        e8_rules = self.checker._load_e8_rules()
        
        assert isinstance(e8_rules, list)
        assert len(e8_rules) > 0
        
        for rule in e8_rules:
            assert "id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule
            assert "check_function" in rule
            assert "remediation" in rule
            assert rule["id"].startswith("E8-")

    def test_load_nist_rules(self):
        """Test loading NIST compliance rules."""
        nist_rules = self.checker._load_nist_rules()
        
        assert isinstance(nist_rules, list)
        assert len(nist_rules) > 0
        
        for rule in nist_rules:
            assert "id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule
            assert "check_function" in rule
            assert "remediation" in rule
            assert rule["id"].startswith("NIST-")

    def test_load_owasp_rules(self):
        """Test loading OWASP compliance rules."""
        owasp_rules = self.checker._load_owasp_rules()
        
        assert isinstance(owasp_rules, list)
        assert len(owasp_rules) > 0
        
        for rule in owasp_rules:
            assert "id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule
            assert "check_function" in rule
            assert "remediation" in rule
            assert rule["id"].startswith("OWASP-")

    def test_load_iso27001_rules(self):
        """Test loading ISO 27001 compliance rules."""
        iso_rules = self.checker._load_iso27001_rules()
        
        assert isinstance(iso_rules, list)
        assert len(iso_rules) > 0
        
        for rule in iso_rules:
            assert "id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule
            assert "check_function" in rule
            assert "remediation" in rule
            assert rule["id"].startswith("ISO-")

    def test_load_pci_rules(self):
        """Test loading PCI DSS compliance rules."""
        pci_rules = self.checker._load_pci_rules()
        
        assert isinstance(pci_rules, list)
        assert len(pci_rules) > 0
        
        for rule in pci_rules:
            assert "id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule
            assert "check_function" in rule
            assert "remediation" in rule
            assert rule["id"].startswith("PCI-")

    def test_load_hipaa_rules(self):
        """Test loading HIPAA compliance rules."""
        hipaa_rules = self.checker._load_hipaa_rules()
        
        assert isinstance(hipaa_rules, list)
        assert len(hipaa_rules) > 0
        
        for rule in hipaa_rules:
            assert "id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule
            assert "check_function" in rule
            assert "remediation" in rule
            assert rule["id"].startswith("HIPAA-")

    def test_load_gdpr_rules(self):
        """Test loading GDPR compliance rules."""
        gdpr_rules = self.checker._load_gdpr_rules()
        
        assert isinstance(gdpr_rules, list)
        assert len(gdpr_rules) > 0
        
        for rule in gdpr_rules:
            assert "id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule
            assert "check_function" in rule
            assert "remediation" in rule
            assert rule["id"].startswith("GDPR-")

    def test_load_soc2_rules(self):
        """Test loading SOC2 compliance rules."""
        soc2_rules = self.checker._load_soc2_rules()
        
        assert isinstance(soc2_rules, list)
        assert len(soc2_rules) > 0
        
        for rule in soc2_rules:
            assert "id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule
            assert "check_function" in rule
            assert "remediation" in rule
            assert rule["id"].startswith("SOC2-")

    @patch.object(ComplianceChecker, "_check_framework")
    def test_check(self, mock_check_framework):
        """Test the check method."""
        mock_check_framework.return_value = {
            "status": "success",
            "framework": "e8",
            "total_rules": 8,
            "rules_checked": 8,
            "issues": [
                {
                    "id": "E8-APP-1",
                    "title": "Application Hardening",
                    "description": "Applications should be hardened to reduce the attack surface",
                    "severity": "high",
                    "category": "Application Security",
                    "remediation": "Disable debug mode in production",
                    "files": ["/path/to/config.py"]
                }
            ],
            "compliant": False
        }
        
        results = self.checker.check(
            repository="test-repo",
            branch="main",
            files=self.test_files
        )
        
        assert results["status"] == "success"
        assert results["repository"] == "test-repo"
        assert results["branch"] == "main"
        assert "frameworks" in results
        assert "summary" in results
        
        assert mock_check_framework.call_count == len(self.checker.frameworks)

    def test_check_with_empty_files(self):
        """Test checking with an empty files list."""
        results = self.checker.check(
            repository="empty-repo",
            branch="main",
            files=[]
        )
        
        assert results["status"] == "success"
        assert results["repository"] == "empty-repo"
        assert results["branch"] == "main"
        assert "frameworks" in results
        assert "summary" in results

    @patch.object(ComplianceChecker, "_check_framework")
    def test_check_with_exception(self, mock_check_framework):
        """Test checking when an exception occurs."""
        mock_check_framework.side_effect = Exception("Test exception")
        
        results = self.checker.check(
            repository="test-repo",
            branch="main",
            files=self.test_files
        )
        
        assert "status" in results
        assert "frameworks" in results
        for framework in self.checker.frameworks:
            assert framework in results["frameworks"]
            assert results["frameworks"][framework]["status"] == "error"
            assert "error" in results["frameworks"][framework]

    def test_check_framework(self):
        """Test checking a specific framework."""
        results = self.checker._check_framework("e8", self.test_files)
        
        assert isinstance(results, dict)
        assert "status" in results
        assert "framework" in results
        assert "total_rules" in results
        assert "rules_checked" in results
        assert "issues" in results
        assert "compliant" in results
        
        results = self.checker._check_framework("invalid_framework", self.test_files)
        
        assert isinstance(results, dict)
        assert "status" in results
        assert "error" in results

    @patch("random.random")
    def test_check_framework_with_issues(self, mock_random):
        """Test checking a framework with issues."""
        mock_random.return_value = 0.1
        
        results = self.checker._check_framework("e8", self.test_files)
        
        assert isinstance(results, dict)
        assert results["status"] == "success"
        assert len(results["issues"]) > 0
        assert not results["compliant"]

    @patch("random.random")
    def test_check_framework_without_issues(self, mock_random):
        """Test checking a framework without issues."""
        mock_random.return_value = 0.5
        
        results = self.checker._check_framework("e8", self.test_files)
        
        assert isinstance(results, dict)
        assert results["status"] == "success"
        assert len(results["issues"]) == 0
        assert results["compliant"]

    def test_generate_summary(self):
        """Test generating a summary of results."""
        results = {
            "frameworks": {
                "e8": {
                    "status": "success",
                    "issues": [
                        {"severity": "critical"},
                        {"severity": "high"}
                    ]
                },
                "nist": {
                    "status": "success",
                    "issues": [
                        {"severity": "high"},
                        {"severity": "medium"}
                    ]
                },
                "owasp": {
                    "status": "success",
                    "issues": [
                        {"severity": "low"}
                    ]
                }
            }
        }
        
        summary = self.checker._generate_summary(results)
        
        assert summary["total_issues"] == 5
        assert summary["critical"] == 1
        assert summary["high"] == 2
        assert summary["medium"] == 1
        assert summary["low"] == 1
        assert summary["frameworks_checked"] == 3
        assert summary["compliant_frameworks"] == 0
