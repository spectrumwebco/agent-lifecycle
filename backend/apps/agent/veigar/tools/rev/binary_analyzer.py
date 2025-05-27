"""
Binary analysis tools for security review.
"""

import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class BinaryAnalyzer:
    """
    Analyzes binary files for security vulnerabilities and weaknesses.
    """
    
    def __init__(self):
        """Initialize the binary analyzer."""
        self.findings = []
    
    def analyze_binary(self, binary_data: bytes, file_path: str, binary_type: str = "elf") -> List[Dict[str, Any]]:
        """
        Analyze a binary file for security issues.
        
        Args:
            binary_data: The binary data to analyze
            file_path: Path to the binary file
            binary_type: Type of binary (elf, pe, macho)
            
        Returns:
            List of identified security issues
        """
        self.findings = []
        
        if binary_type == "auto":
            binary_type = self._detect_binary_type(binary_data)
        
        logger.info("Analyzing binary file %s of type %s", file_path, binary_type)
        
        self._check_security_mitigations(binary_data, binary_type)
        self._check_hardcoded_secrets(binary_data)
        self._check_vulnerable_functions(binary_data, binary_type)
        
        return self.findings
    
    def _detect_binary_type(self, binary_data: bytes) -> str:
        """Detect the type of binary file."""
        if binary_data.startswith(b'\x7fELF'):
            return "elf"
        elif binary_data.startswith(b'MZ'):
            return "pe"
        elif binary_data.startswith(b'\xfe\xed\xfa\xce') or binary_data.startswith(b'\xfe\xed\xfa\xcf') or \
             binary_data.startswith(b'\xca\xfe\xba\xbe') or binary_data.startswith(b'\xce\xfa\xed\xfe'):
            return "macho"
        else:
            return "unknown"
    
    def _check_security_mitigations(self, binary_data: bytes, binary_type: str) -> None:
        """Check for missing security mitigations in the binary."""
        if binary_type == "elf":
            if b"GNU_STACK" in binary_data and b"RWE" in binary_data:
                self.findings.append({
                    "type": "missing_nx",
                    "description": "Executable stack detected (missing NX bit protection)",
                    "severity": "high"
                })
            
            if b"ET_EXEC" in binary_data and not b"ET_DYN" in binary_data:
                self.findings.append({
                    "type": "missing_pie",
                    "description": "Binary is not compiled as position-independent executable (PIE)",
                    "severity": "medium"
                })
            
            if not b"GNU_RELRO" in binary_data:
                self.findings.append({
                    "type": "missing_relro",
                    "description": "Binary does not have RELRO protection",
                    "severity": "medium"
                })
        
        elif binary_type == "pe":
            if b"NX" not in binary_data:
                self.findings.append({
                    "type": "missing_dep",
                    "description": "Binary does not have DEP (Data Execution Prevention) enabled",
                    "severity": "high"
                })
            
            if b"DynamicBase" not in binary_data:
                self.findings.append({
                    "type": "missing_aslr",
                    "description": "Binary does not have ASLR support",
                    "severity": "medium"
                })
            
            if b"SafeSEH" not in binary_data:
                self.findings.append({
                    "type": "missing_safeseh",
                    "description": "Binary does not have SafeSEH protection",
                    "severity": "medium"
                })
    
    def _check_hardcoded_secrets(self, binary_data: bytes) -> None:
        """Check for hardcoded secrets in the binary."""
        api_key_patterns = [
            rb'api[_-]?key[=:"\s\']+[A-Za-z0-9]{16,}',
            rb'api[_-]?secret[=:"\s\']+[A-Za-z0-9]{16,}',
            rb'access[_-]?token[=:"\s\']+[A-Za-z0-9]{16,}',
            rb'auth[_-]?token[=:"\s\']+[A-Za-z0-9]{16,}',
            rb'client[_-]?secret[=:"\s\']+[A-Za-z0-9]{16,}',
            rb'secret[_-]?key[=:"\s\']+[A-Za-z0-9]{16,}'
        ]
        
        for pattern in api_key_patterns:
            matches = re.findall(pattern, binary_data)
            if matches:
                self.findings.append({
                    "type": "hardcoded_api_key",
                    "description": "Potential API key or secret found in binary",
                    "severity": "critical",
                    "details": str(matches[:3])  # Limit to first 3 matches to avoid excessive output
                })
                break
        
        password_patterns = [
            rb'password[=:"\s\']+[A-Za-z0-9!@#$%^&*()]{8,}',
            rb'passwd[=:"\s\']+[A-Za-z0-9!@#$%^&*()]{8,}',
            rb'pwd[=:"\s\']+[A-Za-z0-9!@#$%^&*()]{8,}'
        ]
        
        for pattern in password_patterns:
            matches = re.findall(pattern, binary_data)
            if matches:
                self.findings.append({
                    "type": "hardcoded_password",
                    "description": "Potential password found in binary",
                    "severity": "critical",
                    "details": str(matches[:3])  # Limit to first 3 matches
                })
                break
    
    def _check_vulnerable_functions(self, binary_data: bytes, binary_type: str) -> None:
        """Check for use of vulnerable functions in the binary."""
        vulnerable_functions = [
            b"strcpy", b"strcat", b"gets", b"sprintf",
            b"printf", b"fprintf", b"sprintf", b"snprintf",
            b"system", b"popen", b"exec", b"execl", b"execlp", b"execle", b"execv", b"execvp", b"execvpe"
        ]
        
        for func in vulnerable_functions:
            if func in binary_data:
                if func in [b"gets", b"system", b"popen", b"exec"]:
                    severity = "high"
                else:
                    severity = "medium"
                
                self.findings.append({
                    "type": "vulnerable_function",
                    "description": f"Use of potentially vulnerable function: {func.decode()}",
                    "severity": severity
                })
