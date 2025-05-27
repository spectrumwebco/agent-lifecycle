"""
Cryptography analysis tools for security review.
"""

import logging
import re
import json
import math
import subprocess
from typing import Dict, List, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)

class CryptoAnalyzer:
    """
    Analyzes cryptographic implementations for vulnerabilities and weaknesses.
    """
    
    def __init__(self):
        """Initialize the crypto analyzer."""
        self.vulnerabilities = []
    
    def analyze_crypto_code(self, code: str, language: str = "python") -> List[Dict[str, Any]]:
        """
        Analyze code for cryptographic vulnerabilities.
        
        Args:
            code: The code to analyze
            language: The programming language of the code
            
        Returns:
            List of identified cryptographic vulnerabilities
        """
        self.vulnerabilities = []
        
        self._check_weak_algorithms(code, language)
        
        self._check_hardcoded_keys(code, language)
        
        self._check_insecure_random(code, language)
        
        self._check_improper_iv_usage(code, language)
        
        return self.vulnerabilities
        
    def analyze_hash(self, hash_value: str) -> Dict[str, Any]:
        """
        Analyze a hash value to determine its type and attempt to crack it.
        
        Args:
            hash_value: The hash value to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        result = {
            "status": "success",
            "hash": hash_value,
            "hash_type": self._detect_hash_type(hash_value),
            "cracked": None
        }
        
        try:
            process = subprocess.run(
                ["hashcat", "--quiet", "--potfile-disable", "--outfile-format=3", 
                 f"--hash-type={self._get_hashcat_mode(result['hash_type'])}", 
                 hash_value, "/usr/share/wordlists/rockyou.txt"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0 and process.stdout.strip():
                result["cracked"] = process.stdout.strip().split(":")[-1]
            
        except FileNotFoundError:
            result["note"] = "Using simulation mode as hashcat is not available"
            
            common_passwords = ["password", "123456", "admin", "welcome", "qwerty"]
            if hash_value.lower() == "5f4dcc3b5aa765d61d8327deb882cf99":  # MD5 of "password"
                result["cracked"] = "password"
            elif hash_value.lower() == "e10adc3949ba59abbe56e057f20f883e":  # MD5 of "123456"
                result["cracked"] = "123456"
            
        return result
    
    def analyze_ciphertext(self, ciphertext: str) -> Dict[str, Any]:
        """
        Analyze ciphertext to determine encryption algorithm and attempt cryptanalysis.
        
        Args:
            ciphertext: The ciphertext to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        result = {
            "status": "success",
            "ciphertext": ciphertext,
            "detected_algorithm": None,
            "entropy": self._calculate_entropy(ciphertext),
            "possible_keys": [],
            "plaintext_samples": []
        }
        
        if ciphertext.startswith("U2FsdGVkX1"):
            result["detected_algorithm"] = "AES-256-CBC (OpenSSL format)"
        elif re.match(r'^[A-Za-z0-9+/]+={0,2}$', ciphertext):
            result["detected_algorithm"] = "Base64 encoded (unknown algorithm)"
        elif re.match(r'^[0-9a-fA-F]+$', ciphertext):
            result["detected_algorithm"] = "Hex encoded (unknown algorithm)"
        else:
            result["detected_algorithm"] = "Unknown"
        
        try:
            process = subprocess.run(
                ["cryptanalyzer", "--analyze", ciphertext],
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0 and process.stdout.strip():
                try:
                    analysis_result = json.loads(process.stdout)
                    result.update(analysis_result)
                except json.JSONDecodeError:
                    pass
                
        except FileNotFoundError:
            result["note"] = "Using simulation mode as cryptanalysis tools are not available"
            
            if result["entropy"] < 3.0:
                result["possible_keys"].append("Potentially weak encryption key")
                result["plaintext_samples"].append("Potential plaintext sample (simulated)")
            
        return result
    
    def analyze_encryption_scheme(self, scheme: str, key_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze an encryption scheme for vulnerabilities.
        
        Args:
            scheme: The encryption scheme (e.g., RSA, AES)
            key_size: The key size in bits
            
        Returns:
            Dictionary containing analysis results
        """
        result = {
            "status": "success",
            "scheme": scheme,
            "key_size": key_size,
            "vulnerabilities": [],
            "recommendations": []
        }
        
        try:
            process = subprocess.run(
                ["crypto-analyzer", "--scheme", scheme, "--key-size", str(key_size)],
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0 and process.stdout.strip():
                try:
                    analysis_result = json.loads(process.stdout)
                    result["vulnerabilities"] = analysis_result.get("vulnerabilities", [])
                    result["recommendations"] = analysis_result.get("recommendations", [])
                except json.JSONDecodeError:
                    pass
                
        except FileNotFoundError:
            result["note"] = "Using simulation mode as encryption analysis tools are not available"
            
            if scheme.upper() == "RSA":
                if key_size and key_size < 2048:
                    result["vulnerabilities"].append({
                        "title": "Weak RSA key size",
                        "description": f"RSA key size of {key_size} bits is below recommended minimum of 2048 bits",
                        "severity": "high",
                        "remediation": "Increase key size to at least 2048 bits, preferably 4096 bits"
                    })
                    result["recommendations"].append("Increase RSA key size to at least 2048 bits")
                
                result["recommendations"].append("Implement proper key management")
                result["recommendations"].append("Use padding schemes like OAEP for RSA encryption")
                
            elif scheme.upper() == "AES":
                if key_size and key_size < 128:
                    result["vulnerabilities"].append({
                        "title": "Weak AES key size",
                        "description": f"AES key size of {key_size} bits is below the minimum of 128 bits",
                        "severity": "critical",
                        "remediation": "Increase key size to at least 128 bits, preferably 256 bits"
                    })
                    result["recommendations"].append("Increase AES key size to at least 128 bits")
                
                result["recommendations"].append("Use a secure mode of operation (GCM, CBC with proper padding)")
                result["recommendations"].append("Ensure proper IV management for each encryption operation")
            
        return result
    
    def comprehensive_analysis(self, hash_value=None, ciphertext=None, encryption_scheme=None, key_size=None) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of cryptographic artifacts.
        
        Args:
            hash_value: Optional hash value to analyze
            ciphertext: Optional ciphertext to analyze
            encryption_scheme: Optional encryption scheme to analyze
            key_size: Optional key size for the encryption scheme
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        result = {
            "status": "success",
            "summary": {}
        }
        
        if hash_value:
            result["hash_analysis"] = self.analyze_hash(hash_value)
            
        if ciphertext:
            result["ciphertext_analysis"] = self.analyze_ciphertext(ciphertext)
            
        if encryption_scheme:
            result["scheme_analysis"] = self.analyze_encryption_scheme(
                encryption_scheme, 
                int(key_size) if key_size is not None else None
            )
        
        all_vulnerabilities = []
        if hash_value and result["hash_analysis"].get("cracked"):
            all_vulnerabilities.append({
                "type": "weak_hash",
                "description": f"Hash was successfully cracked: {result['hash_analysis']['cracked']}",
                "severity": "high"
            })
            
        if encryption_scheme and "scheme_analysis" in result:
            all_vulnerabilities.extend(result["scheme_analysis"].get("vulnerabilities", []))
            
        result["summary"] = self._generate_summary(all_vulnerabilities)
        
        return result
    
    def _detect_hash_type(self, hash_value: str) -> str:
        """
        Detect the type of hash based on its length and pattern.
        
        Args:
            hash_value: The hash value to analyze
            
        Returns:
            String indicating the detected hash type
        """
        hash_value = hash_value.lower()
        
        if len(hash_value) == 32 and re.match(r'^[0-9a-f]{32}$', hash_value):
            return "MD5"
        elif len(hash_value) == 40 and re.match(r'^[0-9a-f]{40}$', hash_value):
            return "SHA-1"
        elif len(hash_value) == 64 and re.match(r'^[0-9a-f]{64}$', hash_value):
            return "SHA-256"
        elif len(hash_value) == 128 and re.match(r'^[0-9a-f]{128}$', hash_value):
            return "SHA-512"
        elif len(hash_value) == 16 and re.match(r'^[0-9a-f]{16}$', hash_value):
            return "MD4"
        elif len(hash_value) == 56 and re.match(r'^[0-9a-f]{56}$', hash_value):
            return "SHA-224"
        elif len(hash_value) == 96 and re.match(r'^[0-9a-f]{96}$', hash_value):
            return "SHA-384"
        
        return "Unknown"
    
    def _get_hashcat_mode(self, hash_type: str) -> int:
        """
        Get the hashcat mode number for a given hash type.
        
        Args:
            hash_type: The hash type (e.g., MD5, SHA-1)
            
        Returns:
            Integer representing the hashcat mode
        """
        modes = {
            "MD5": 0,
            "SHA-1": 100,
            "SHA-256": 1400,
            "SHA-512": 1700,
            "MD4": 900,
            "SHA-224": 1300,
            "SHA-384": 10800
        }
        
        return modes.get(hash_type, 0)
    
    def _calculate_entropy(self, data: str) -> float:
        """
        Calculate the Shannon entropy of data.
        
        Args:
            data: The data to calculate entropy for
            
        Returns:
            Float representing the entropy value
        """
        if not data:
            return 0.0
            
        entropy = 0.0
        counter = Counter(data)
        length = len(data)
        
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
            
        return entropy
    
    def _generate_summary(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of vulnerabilities by severity.
        
        Args:
            vulnerabilities: List of vulnerability dictionaries
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total_vulnerabilities": len(vulnerabilities),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "").lower()
            if severity in summary:
                summary[severity] += 1
        
        return summary
    
    def _check_weak_algorithms(self, code: str, language: str) -> None:
        """Check for weak cryptographic algorithms."""
        weak_algos = {
            "python": [
                (r"\bMD5\b", "MD5 is a weak hashing algorithm"),
                (r"\bSHA1\b", "SHA1 is considered weak for cryptographic purposes"),
                (r"\bDES\b", "DES encryption is considered weak"),
                (r"\bRC4\b", "RC4 encryption is vulnerable to various attacks"),
                (r"\bECB\b", "ECB mode doesn't provide semantic security")
            ],
            "go": [
                (r"\bMD5\b", "MD5 is a weak hashing algorithm"),
                (r"\bSHA1\b", "SHA1 is considered weak for cryptographic purposes"),
                (r"\bcrypto/des\b", "DES encryption is considered weak"),
                (r"\bECB\b", "ECB mode doesn't provide semantic security")
            ],
            "javascript": [
                (r"\bMD5\b", "MD5 is a weak hashing algorithm"),
                (r"\bSHA1\b", "SHA1 is considered weak for cryptographic purposes"),
                (r"\bDES\b", "DES encryption is considered weak"),
                (r"\bRC4\b", "RC4 encryption is vulnerable to various attacks")
            ]
        }
        
        lang_patterns = weak_algos.get(language, weak_algos["python"])
        
        for pattern, description in lang_patterns:
            if re.search(pattern, code):
                self.vulnerabilities.append({
                    "type": "weak_algorithm",
                    "description": description,
                    "severity": "high"
                })
    
    def _check_hardcoded_keys(self, code: str, language: str) -> None:
        """Check for hardcoded cryptographic keys."""
        key_patterns = {
            "python": [
                r"key\s*=\s*['\"][0-9a-fA-F]{16,}['\"]",
                r"secret\s*=\s*['\"][0-9a-fA-F]{16,}['\"]",
                r"password\s*=\s*['\"][^'\"]{8,}['\"]"
            ],
            "go": [
                r"key\s*:=\s*\[[^\]]+\]",
                r"key\s*:=\s*\"[0-9a-fA-F]{16,}\"",
                r"secret\s*:=\s*\"[0-9a-fA-F]{16,}\""
            ],
            "javascript": [
                r"const\s+key\s*=\s*['\"][0-9a-fA-F]{16,}['\"]",
                r"let\s+key\s*=\s*['\"][0-9a-fA-F]{16,}['\"]",
                r"var\s+key\s*=\s*['\"][0-9a-fA-F]{16,}['\"]"
            ]
        }
        
        
        lang_patterns = key_patterns.get(language, key_patterns["python"])
        
        for pattern in lang_patterns:
            if re.search(pattern, code):
                self.vulnerabilities.append({
                    "type": "hardcoded_key",
                    "description": "Hardcoded cryptographic keys or passwords detected",
                    "severity": "critical"
                })
                break
    
    def _check_insecure_random(self, code: str, language: str) -> None:
        """Check for insecure random number generation."""
        insecure_random_patterns = {
            "python": [
                (r"\brandom\.[^\n]*\b", "Python's 'random' module is not cryptographically secure"),
                (r"\bmathematical_random\b", "Non-cryptographic random function usage")
            ],
            "go": [
                (r"\bmath/rand\b", "Go's math/rand is not cryptographically secure"),
                (r"\bmathematical_random\b", "Non-cryptographic random function usage")
            ],
            "javascript": [
                (r"\bMath\.random\(\)", "JavaScript's Math.random() is not cryptographically secure"),
                (r"\bmathematical_random\b", "Non-cryptographic random function usage")
            ]
        }
        
        lang_patterns = insecure_random_patterns.get(language, insecure_random_patterns["python"])
        
        for pattern, description in lang_patterns:
            if re.search(pattern, code):
                self.vulnerabilities.append({
                    "type": "insecure_random",
                    "description": description,
                    "severity": "medium"
                })
                break
    
    def _check_improper_iv_usage(self, code: str, language: str) -> None:
        """Check for improper IV usage."""
        improper_iv_patterns = {
            "python": [
                (r"iv\s*=\s*b?['\"]0+['\"]", "Zero initialization vector detected"),
                (r"iv\s*=\s*b?['\"][^\n]{1,8}['\"]", "Short initialization vector detected")
            ],
            "go": [
                (r"iv\s*:=\s*\[\]byte\{0+\}", "Zero initialization vector detected"),
                (r"iv\s*:=\s*\[\]byte\{[^\}]{1,8}\}", "Short initialization vector detected")
            ],
            "javascript": [
                (r"iv\s*=\s*['\"]0+['\"]", "Zero initialization vector detected"),
                (r"iv\s*=\s*new\s+Uint8Array\(\[0+\]\)", "Zero initialization vector detected")
            ]
        }
        
        lang_patterns = improper_iv_patterns.get(language, improper_iv_patterns["python"])
        
        for pattern, description in lang_patterns:
            if re.search(pattern, code):
                self.vulnerabilities.append({
                    "type": "improper_iv",
                    "description": description,
                    "severity": "high"
                })
                break
