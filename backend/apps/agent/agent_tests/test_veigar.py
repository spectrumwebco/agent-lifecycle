"""
Basic tests for the Veigar agent to verify the restructuring works.
"""

import pytest
import os
from pathlib import Path

def test_veigar_config_exists():
    """Test that the Veigar config directory exists."""
    config_path = Path("/home/ubuntu/repos/agent_runtime/backend/apps/python_agent/veigar/config")
    assert config_path.exists(), f"Veigar config directory does not exist at {config_path}"

def test_veigar_tools_directory_exists():
    """Test that the Veigar tools directory exists."""
    tools_path = Path("/home/ubuntu/repos/agent_runtime/backend/apps/python_agent/veigar/tools")
    assert tools_path.exists(), f"Veigar tools directory does not exist at {tools_path}"
    
    assert (tools_path / "crypto").exists(), "Crypto tools directory does not exist"
    assert (tools_path / "pwn").exists(), "Pwn tools directory does not exist"
    assert (tools_path / "rev").exists(), "Rev tools directory does not exist"
    assert (tools_path / "web").exists(), "Web tools directory does not exist"
    assert (tools_path / "forensics").exists(), "Forensics tools directory does not exist"
