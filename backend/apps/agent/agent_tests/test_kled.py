"""
Basic tests for the Kled agent to verify the restructuring works.
"""

import pytest
import os
from pathlib import Path

def test_kled_directory_structure():
    """Test that the Kled agent directory structure exists."""
    base_path = Path("/home/ubuntu/repos/agent_runtime/backend/apps/python_agent/kled")
    assert base_path.exists(), f"Kled directory does not exist at {base_path}"
    
    assert (base_path / "agent").exists(), "Agent directory does not exist"
    assert (base_path / "tools").exists(), "Tools directory does not exist"
    assert (base_path / "config").exists(), "Config directory does not exist"
    assert (base_path / "django_integration").exists(), "Django integration directory does not exist"
    assert (base_path / "django_models").exists(), "Django models directory does not exist"
    assert (base_path / "django_views").exists(), "Django views directory does not exist"
    assert (base_path / "go_integration").exists(), "Go integration directory does not exist"
