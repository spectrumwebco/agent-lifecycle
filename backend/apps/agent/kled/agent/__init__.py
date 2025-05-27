"""
Kled agent module.

This module provides the core agent implementation for the Kled software engineering agent.
"""

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent.parent.parent.parent
CONFIG_DIR = Path(os.getenv("SWE_AGENT_CONFIG_DIR", PACKAGE_DIR.parent / "config"))

__all__ = [
    "PACKAGE_DIR",
    "CONFIG_DIR",
    "REPO_ROOT",
]
