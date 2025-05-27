"""
Security logging tools for Veigar.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any


logger = logging.getLogger(__name__)


class SecurityLogger:
    """
    Specialized logger for security events and findings.
    """

    def __init__(self, log_dir: str = "/tmp/veigar_logs"):
        """
        Initialize the security logger.

        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir

        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(log_dir, f"security_{timestamp}.log")

        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        self.security_logger = logging.getLogger("veigar.security")
        self.security_logger.setLevel(logging.INFO)
        self.security_logger.addHandler(file_handler)

    def log_security_event(
        self, event_type: str, details: Dict[str, Any], severity: str = "info"
    ) -> None:
        """
        Log a security event.

        Args:
            event_type: Type of security event
            details: Details of the event
            severity: Severity level (info, warning, error, critical)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details
        }

        log_message = json.dumps(log_entry)

        if severity == "info":
            self.security_logger.info(log_message)
        elif severity == "warning":
            self.security_logger.warning(log_message)
        elif severity == "error":
            self.security_logger.error(log_message)
        elif severity == "critical":
            self.security_logger.critical(log_message)
        else:
            self.security_logger.info(log_message)

    def log_vulnerability(self, vulnerability: Dict[str, Any]) -> None:
        """
        Log a detected vulnerability.

        Args:
            vulnerability: Vulnerability details
        """
        severity = vulnerability.get("severity", "info")

        self.log_security_event(
            event_type="vulnerability_detected",
            details=vulnerability,
            severity=self._map_severity(severity)
        )

    def log_scan_results(self, scan_type: str, results: Dict[str, Any]) -> None:
        """
        Log the results of a security scan.

        Args:
            scan_type: Type of security scan
            results: Scan results
        """
        self.log_security_event(
            event_type=f"{scan_type}_scan_completed",
            details=results,
            severity="info"
        )

    def _map_severity(self, severity: str) -> str:
        """Map vulnerability severity to log severity."""
        severity_map = {
            "critical": "critical",
            "high": "error",
            "medium": "warning",
            "low": "info",
            "info": "info"
        }

        return severity_map.get(severity.lower(), "info")
