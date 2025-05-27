"""
Tests for the Veigar crypto analyzer.

This module contains tests for the crypto analyzer component of the Veigar agent.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import json

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from veigar.tools.crypto.analyzer import CryptoAnalyzer


class TestCryptoAnalyzer:
    """Test suite for the CryptoAnalyzer class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.analyzer = CryptoAnalyzer()
        self.test_file = "/path/to/test_file.bin"
        self.test_hash = "5f4dcc3b5aa765d61d8327deb882cf99"
        self.test_ciphertext = "U2FsdGVkX1/R+WzJcxgvX/9MgMSDAWPL"

    def test_initialization(self):
        """Test that the analyzer initializes correctly."""
        assert hasattr(self.analyzer, "analyze_hash")
        assert hasattr(self.analyzer, "analyze_ciphertext")
        assert hasattr(self.analyzer, "analyze_encryption_scheme")

    @patch("subprocess.run")
    def test_analyze_hash_with_tool_available(self, mock_run):
        """Test analyzing a hash when hashcat is available."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Hash: 5f4dcc3b5aa765d61d8327deb882cf99\nType: MD5\nCracked: password"
        mock_run.return_value = mock_process
        
        results = self.analyzer.analyze_hash(self.test_hash)
        
        assert results["status"] == "success"
        assert results["hash"] == self.test_hash
        assert "hash_type" in results
        assert "cracked" in results
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "hashcat" in args[0]

    @patch("subprocess.run")
    def test_analyze_hash_with_tool_unavailable(self, mock_run):
        """Test analyzing a hash when hashcat is not available."""
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'hashcat'")
        
        results = self.analyzer.analyze_hash(self.test_hash)
        
        assert results["status"] == "success"  # Should still succeed with fallback
        assert results["hash"] == self.test_hash
        assert "hash_type" in results
        assert "note" in results
        assert "simulation" in results["note"].lower()

    @patch("subprocess.run")
    def test_analyze_ciphertext_with_tool_available(self, mock_run):
        """Test analyzing ciphertext when cryptanalysis tools are available."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = json.dumps({
            "ciphertext": self.test_ciphertext,
            "detected_algorithm": "AES-256-CBC",
            "entropy": 3.8,
            "possible_keys": ["key1", "key2"],
            "plaintext_samples": ["sample1", "sample2"]
        })
        mock_run.return_value = mock_process
        
        results = self.analyzer.analyze_ciphertext(self.test_ciphertext)
        
        assert results["status"] == "success"
        assert results["ciphertext"] == self.test_ciphertext
        assert "detected_algorithm" in results
        assert "entropy" in results
        assert "possible_keys" in results
        assert "plaintext_samples" in results
        
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_analyze_ciphertext_with_tool_unavailable(self, mock_run):
        """Test analyzing ciphertext when cryptanalysis tools are not available."""
        mock_run.side_effect = FileNotFoundError("No such file or directory")
        
        results = self.analyzer.analyze_ciphertext(self.test_ciphertext)
        
        assert results["status"] == "success"  # Should still succeed with fallback
        assert results["ciphertext"] == self.test_ciphertext
        assert "detected_algorithm" in results
        assert "entropy" in results
        assert "note" in results
        assert "simulation" in results["note"].lower()

    @patch("subprocess.run")
    def test_analyze_encryption_scheme(self, mock_run):
        """Test analyzing an encryption scheme."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = json.dumps({
            "scheme": "RSA",
            "key_size": 2048,
            "vulnerabilities": [
                {
                    "title": "Weak key size",
                    "description": "RSA key size is less than recommended 3072 bits",
                    "severity": "medium",
                    "remediation": "Increase key size to at least 3072 bits"
                }
            ],
            "recommendations": [
                "Use a key size of at least 3072 bits",
                "Implement proper key management"
            ]
        })
        mock_run.return_value = mock_process
        
        results = self.analyzer.analyze_encryption_scheme("RSA", key_size=2048)
        
        assert results["status"] == "success"
        assert results["scheme"] == "RSA"
        assert results["key_size"] == 2048
        assert "vulnerabilities" in results
        assert "recommendations" in results
        assert len(results["vulnerabilities"]) > 0
        assert len(results["recommendations"]) > 0
        
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_analyze_encryption_scheme_with_tool_unavailable(self, mock_run):
        """Test analyzing an encryption scheme when tools are not available."""
        mock_run.side_effect = FileNotFoundError("No such file or directory")
        
        results = self.analyzer.analyze_encryption_scheme("RSA", key_size=2048)
        
        assert results["status"] == "success"  # Should still succeed with fallback
        assert results["scheme"] == "RSA"
        assert results["key_size"] == 2048
        assert "vulnerabilities" in results
        assert "recommendations" in results
        assert "note" in results
        assert "simulation" in results["note"].lower()

    def test_detect_hash_type(self):
        """Test detecting hash types."""
        md5_hash = "5f4dcc3b5aa765d61d8327deb882cf99"
        assert self.analyzer._detect_hash_type(md5_hash) == "MD5"
        
        sha1_hash = "5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8"
        assert self.analyzer._detect_hash_type(sha1_hash) == "SHA-1"
        
        sha256_hash = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
        assert self.analyzer._detect_hash_type(sha256_hash) == "SHA-256"
        
        unknown_hash = "not_a_real_hash"
        assert self.analyzer._detect_hash_type(unknown_hash) == "Unknown"

    def test_calculate_entropy(self):
        """Test calculating entropy of data."""
        low_entropy = "AAAAAAAAAAAAAAAAAAAA"
        low_result = self.analyzer._calculate_entropy(low_entropy)
        assert low_result < 1.0  # Low entropy should be close to 0
        
        high_entropy = "Th1s!Is@High#Entropy$Data%With^Many&Different*Characters"
        high_result = self.analyzer._calculate_entropy(high_entropy)
        assert high_result > 3.0  # High entropy should be higher
        
        empty_result = self.analyzer._calculate_entropy("")
        assert empty_result == 0.0  # Empty data should have zero entropy

    def test_comprehensive_analysis(self):
        """Test comprehensive analysis of cryptographic artifacts."""
        with patch.object(self.analyzer, "analyze_hash") as mock_analyze_hash, \
             patch.object(self.analyzer, "analyze_ciphertext") as mock_analyze_ciphertext, \
             patch.object(self.analyzer, "analyze_encryption_scheme") as mock_analyze_scheme:
            
            mock_analyze_hash.return_value = {"status": "success", "hash_type": "MD5"}
            mock_analyze_ciphertext.return_value = {"status": "success", "detected_algorithm": "AES"}
            mock_analyze_scheme.return_value = {"status": "success", "vulnerabilities": []}
            
            results = self.analyzer.comprehensive_analysis(
                hash_value=self.test_hash,
                ciphertext=self.test_ciphertext,
                encryption_scheme="AES",
                key_size=256
            )
            
            assert results["status"] == "success"
            assert "hash_analysis" in results
            assert "ciphertext_analysis" in results
            assert "scheme_analysis" in results
            assert results["hash_analysis"]["hash_type"] == "MD5"
            assert results["ciphertext_analysis"]["detected_algorithm"] == "AES"
            
            mock_analyze_hash.assert_called_once()
            mock_analyze_ciphertext.assert_called_once()
            mock_analyze_scheme.assert_called_once()

    def test_generate_summary(self):
        """Test generating a summary of vulnerabilities."""
        vulnerabilities = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"}
        ]
        
        summary = self.analyzer._generate_summary(vulnerabilities)
        
        assert summary["total_vulnerabilities"] == 5
        assert summary["critical"] == 1
        assert summary["high"] == 2
        assert summary["medium"] == 1
        assert summary["low"] == 1
