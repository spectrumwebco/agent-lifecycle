"""
Test module for Neovim bulk terminal management functionality.
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.tools.neovim_tool import NeovimTool


class TestNeovimBulkTerminals(unittest.TestCase):
    """Test cases for Neovim bulk terminal management."""

    def setUp(self):
        """Set up test environment."""
        self.neovim_tool = NeovimTool()
        self.neovim_tool.neovim_api_base = "http://localhost:8090/neovim"
        self.neovim_tool.active_instances = {}
        self.neovim_tool.background_tasks = {}

    @patch('requests.post')
    def test_start_bulk_instances(self, mock_post):
        """Test starting multiple Neovim instances in bulk."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = asyncio.run(self.neovim_tool.start_bulk_instances(3, prefix="test_"))

        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["test_0", "test_1", "test_2"])
        self.assertEqual(mock_post.call_count, 3)
        
        self.assertEqual(len(self.neovim_tool.active_instances), 3)
        self.assertTrue("test_0" in self.neovim_tool.active_instances)
        self.assertTrue("test_1" in self.neovim_tool.active_instances)
        self.assertTrue("test_2" in self.neovim_tool.active_instances)

    @patch('requests.post')
    def test_execute_in_all(self, mock_post):
        """Test executing a command in all active Neovim instances."""
        self.neovim_tool.active_instances = {
            "test_0": True,
            "test_1": True,
            "test_2": True
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": "Command executed"}
        mock_post.return_value = mock_response

        result = asyncio.run(self.neovim_tool.execute_in_all(":echo 'Hello'<CR>"))

        self.assertEqual(len(result), 3)
        self.assertTrue("test_0" in result)
        self.assertTrue("test_1" in result)
        self.assertTrue("test_2" in result)
        self.assertEqual(mock_post.call_count, 3)

    @patch('requests.post')
    def test_execute_agent_framework_command(self, mock_post):
        """Test executing a command through the agent_framework terminal integration."""
        self.neovim_tool.active_instances = {"test_instance": True}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": "Command executed"}
        mock_post.return_value = mock_response

        result = asyncio.run(self.neovim_tool.execute_agent_framework_command(
            "test_instance", "ls -la", "terminal_1"
        ))

        self.assertEqual(result, {"output": "Command executed"})
        self.assertEqual(mock_post.call_count, 1)
        
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["command"], ":terminal ls -la<CR>")

    @patch('requests.post')
    def test_cleanup_bulk_instances(self, mock_post):
        """Test cleaning up multiple Neovim instances."""
        self.neovim_tool.active_instances = {
            "test_0": True,
            "test_1": True,
            "test_2": True
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        asyncio.run(self.neovim_tool.cleanup())

        self.assertEqual(len(self.neovim_tool.active_instances), 0)
        self.assertEqual(mock_post.call_count, 3)


if __name__ == "__main__":
    unittest.main()
