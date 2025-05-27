"""
Test script for Neovim integration in agent_runtime.
"""

import asyncio
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.tools.neovim_tool import NeovimTool


class MockResponse:
    """Mock response for requests."""
    
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self.json_data = json_data or {}
        
    def json(self):
        """Return JSON data."""
        return self.json_data


class TestNeovimTool(unittest.TestCase):
    """Test cases for NeovimTool."""
    
    def setUp(self):
        """Set up test environment."""
        self.neovim = NeovimTool()
        self.instance_id = "test_instance"
        self.test_file = "/tmp/neovim_test.txt"
        
        with open(self.test_file, "w") as f:
            f.write("This is a test file for Neovim integration.\n")
            f.write("Line 2\n")
            f.write("Line 3\n")
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    @patch("requests.post")
    async def test_start_instance(self, mock_post):
        """Test starting a Neovim instance."""
        mock_post.return_value = MockResponse(200, {"status": "success"})
        
        success = await self.neovim.start_instance(self.instance_id)
        
        self.assertTrue(success)
        self.assertTrue(self.instance_id in self.neovim.active_instances)
        mock_post.assert_called_once_with(
            f"{self.neovim.neovim_api_base}/start",
            json={"id": self.instance_id}
        )
    
    @patch("requests.post")
    async def test_stop_instance(self, mock_post):
        """Test stopping a Neovim instance."""
        mock_post.return_value = MockResponse(200, {"status": "success"})
        self.neovim.active_instances[self.instance_id] = True
        
        success = await self.neovim.stop_instance(self.instance_id)
        
        self.assertTrue(success)
        self.assertFalse(self.instance_id in self.neovim.active_instances)
        mock_post.assert_called_once_with(
            f"{self.neovim.neovim_api_base}/stop",
            json={"id": self.instance_id}
        )
    
    @patch("requests.post")
    async def test_execute_command(self, mock_post):
        """Test executing a command in Neovim."""
        mock_post.return_value = MockResponse(200, {"result": "success"})
        self.neovim.active_instances[self.instance_id] = True
        
        result = await self.neovim.execute_command(
            self.instance_id,
            "Go# Added by Neovim integration test<ESC>:w<CR>"
        )
        
        self.assertEqual(result, {"result": "success"})
        mock_post.assert_called_once_with(
            f"{self.neovim.neovim_api_base}/execute",
            json={"id": self.instance_id, "command": "Go# Added by Neovim integration test<ESC>:w<CR>"}
        )
    
    @patch("requests.post")
    async def test_execute_command_with_file(self, mock_post):
        """Test executing a command with a file in Neovim."""
        mock_post.side_effect = [
            MockResponse(200, {"result": "file_opened"}),
            MockResponse(200, {"result": "command_executed"})
        ]
        self.neovim.active_instances[self.instance_id] = True
        
        result = await self.neovim.execute_command(
            self.instance_id,
            "Go# Added by test<ESC>:w<CR>",
            file=self.test_file
        )
        
        self.assertEqual(result, {"result": "command_executed"})
        self.assertEqual(mock_post.call_count, 2)
    
    @patch("requests.post")
    async def test_execute_command_background(self, mock_post):
        """Test executing a command in background."""
        mock_post.return_value = MockResponse(200, {"result": "success"})
        self.neovim.active_instances[self.instance_id] = True
        
        result = await self.neovim.execute_command(
            self.instance_id,
            ":sleep 2<CR>:w<CR>",
            background=True
        )
        
        self.assertTrue("status" in result)
        self.assertEqual(result["status"], "running_in_background")
        self.assertTrue("task_id" in result)
        self.assertTrue(result["task_id"] in self.neovim.background_tasks)
    
    @patch("requests.get")
    async def test_get_state(self, mock_get):
        """Test getting Neovim state."""
        mock_get.return_value = MockResponse(200, {"mode": "normal", "file": self.test_file})
        self.neovim.active_instances[self.instance_id] = True
        
        state = await self.neovim.get_state(self.instance_id)
        
        self.assertEqual(state, {"mode": "normal", "file": self.test_file})
        mock_get.assert_called_once_with(
            f"{self.neovim.neovim_api_base}/state",
            params={"id": self.instance_id}
        )
    
    async def test_background_tasks(self):
        """Test background task management."""
        mock_task = MagicMock()
        mock_task.done.return_value = False
        task_id = f"{self.instance_id}_0"
        self.neovim.background_tasks[task_id] = mock_task
        
        tasks = await self.neovim.get_background_tasks()
        self.assertEqual(tasks, [task_id])
        
        status = await self.neovim.check_background_task(task_id)
        self.assertEqual(status, {"status": "running"})
        
        mock_task.done.return_value = True
        mock_task.result.return_value = {"result": "success"}
        status = await self.neovim.check_background_task(task_id)
        self.assertEqual(status, {"status": "completed", "result": {"result": "success"}})
        
        mock_task.done.return_value = False
        result = await self.neovim.cancel_background_task(task_id)
        self.assertEqual(result, {"status": "cancelled"})
        mock_task.cancel.assert_called_once()
    
    @patch("requests.post")
    async def test_cleanup(self, mock_post):
        """Test cleanup method."""
        mock_post.return_value = MockResponse(200, {"status": "success"})
        
        self.neovim.active_instances[self.instance_id] = True
        mock_task = MagicMock()
        mock_task.done.return_value = False
        task_id = f"{self.instance_id}_0"
        self.neovim.background_tasks[task_id] = mock_task
        
        await self.neovim.cleanup()
        
        self.assertEqual(len(self.neovim.background_tasks), 0)
        self.assertEqual(len(self.neovim.active_instances), 0)
        mock_task.cancel.assert_called_once()
        mock_post.assert_called_once()


async def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNeovimTool)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Starting Neovim integration tests with mocks...")
    success = asyncio.run(run_tests())
    print(f"Tests {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
