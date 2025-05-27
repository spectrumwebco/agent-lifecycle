"""
Integration tests for Neovim in the Python agent.

This module provides integration tests for the Neovim functionality
in the Python agent, including API service, parallel workflow, and plugins.
"""

import asyncio
import os
import sys
import unittest
import requests
import json
import time
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.api.neovim.routes import router as neovim_router
from agent.tools.neovim_tool import neovim_tool
from agent.tools.parallel_workflow import parallel_workflow_manager
from agent.tools.workflow_integration import workflow_integration
from agent.tools.test_parallel_workflow import test_parallel_workflow, test_plugin_integration


class TestNeovimAPI(unittest.TestCase):
    """Test the Neovim API service."""

    def setUp(self):
        """Set up the test environment."""
        self.api_base = "http://localhost:8090/neovim"
        self.instance_id = f"test_instance_{int(time.time())}"
        
        self.requests_patch = patch('agent.tools.neovim_tool.requests')
        self.mock_requests = self.requests_patch.start()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        self.mock_requests.post.return_value = mock_response
        self.mock_requests.get.return_value = mock_response

    def tearDown(self):
        """Clean up after tests."""
        self.requests_patch.stop()

    def test_start_instance(self):
        """Test starting a Neovim instance."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            neovim_tool.start_instance(self.instance_id)
        )
        
        self.assertTrue(result)
        self.mock_requests.post.assert_called_with(
            f"{neovim_tool.neovim_api_base}/start",
            json={"id": self.instance_id, "config": {}}
        )
        
        loop.close()

    def test_execute_command(self):
        """Test executing a command in Neovim."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        command = ":echo 'Hello'<CR>"
        
        result = loop.run_until_complete(
            neovim_tool.execute_command(self.instance_id, command)
        )
        
        self.assertEqual(result, {"status": "success"})
        self.mock_requests.post.assert_called_with(
            f"{neovim_tool.neovim_api_base}/execute",
            json={"id": self.instance_id, "command": command}
        )
        
        loop.close()

    def test_plugin_command(self):
        """Test executing a plugin command in Neovim."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        command = ":lua require('tmux').resize_direction('h', 10)<CR>"
        
        result = loop.run_until_complete(
            neovim_tool.execute_command(
                self.instance_id, command, plugin="tmux"
            )
        )
        
        self.assertEqual(result, {"status": "success"})
        
        loop.close()


class TestParallelWorkflow(unittest.TestCase):
    """Test the parallel workflow capabilities."""

    def test_workflow_integration(self):
        """Test the workflow integration."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(test_parallel_workflow())
        
        self.assertTrue(result)
        
        loop.close()

    def test_plugin_integration(self):
        """Test the plugin integration."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(test_plugin_integration())
        
        self.assertTrue(result)
        
        loop.close()


class TestNeovimRoutes(unittest.TestCase):
    """Test the Neovim API routes."""

    def test_router_endpoints(self):
        """Test that the router has the expected endpoints."""
        routes = [route.path for route in neovim_router.routes]
        
        self.assertIn("/start", routes)
        self.assertIn("/stop", routes)
        self.assertIn("/execute", routes)
        self.assertIn("/state", routes)
        self.assertIn("/instances", routes)


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == "__main__":
    run_tests()
