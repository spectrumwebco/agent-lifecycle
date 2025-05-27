"""
Mock docker deployment module for local development.
"""

from typing import Dict, Any, Optional, Union, List
from ..deployment.abstract import AbstractDeployment


class DockerDeployment(AbstractDeployment):
    """Mock Docker deployment."""
    
    def __init__(self, config):
        self.config = config
        self.runtime = MockRuntime()
    
    async def start(self):
        """Start deployment."""
        print("Mock Docker deployment started")
    
    async def stop(self):
        """Stop deployment."""
        print("Mock Docker deployment stopped")


class MockRuntime:
    """Mock runtime for Docker deployment."""
    
    async def create_session(self, request):
        """Create session."""
        return {"status": "success"}
    
    async def run_in_session(self, action):
        """Run in session."""
        return MockResponse(output="Mock output", exit_code=0)
    
    async def read_file(self, request):
        """Read file."""
        return MockFileResponse(content="Mock file content")
    
    async def write_file(self, request):
        """Write file."""
        return {"status": "success"}
    
    async def execute(self, command):
        """Execute command."""
        return {"status": "success"}


class MockResponse:
    """Mock response for run_in_session."""
    
    def __init__(self, output="", exit_code=0):
        self.output = output
        self.exit_code = exit_code


class MockFileResponse:
    """Mock response for read_file."""
    
    def __init__(self, content=""):
        self.content = content
