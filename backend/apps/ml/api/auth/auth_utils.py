"""
Authentication utilities for ML Infrastructure API Client.

This module provides utilities for authentication with the ML Infrastructure API.
"""

import os
import time
import logging
import requests
from typing import Dict, Optional, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AuthManager:
    """Authentication manager for ML Infrastructure API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        token_expiry: Optional[int] = None,
    ):
        """Initialize the authentication manager."""
        self.base_url = base_url or os.environ.get("ML_API_BASE_URL")
        self.username = username or os.environ.get("ML_API_USERNAME")
        self.password = password or os.environ.get("ML_API_PASSWORD")
        self.token = token
        self.token_expiry = token_expiry or 0

    def get_auth_token(self) -> str:
        """Get or refresh the authentication token."""
        if self.token and time.time() < self.token_expiry:
            return self.token

        try:
            auth_response = requests.post(
                f"{self.base_url}/token",
                data={
                    "username": self.username,
                    "password": self.password,
                    "grant_type": "password",
                },
                timeout=10,
            )

            auth_response.raise_for_status()
            token_data = auth_response.json()
            self.token = token_data["access_token"]
            self.token_expiry = time.time() + token_data["expires_in"]
            return self.token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get authentication token: {e}")
            raise Exception(f"Authentication failed: {e}")

    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        token = self.get_auth_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_env(cls) -> "AuthManager":
        """Create an AuthManager from environment variables."""
        return cls(
            base_url=os.environ.get("ML_API_BASE_URL"),
            username=os.environ.get("ML_API_USERNAME"),
            password=os.environ.get("ML_API_PASSWORD"),
        )
