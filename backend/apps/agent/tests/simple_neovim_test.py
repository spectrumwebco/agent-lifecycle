"""
Simplified test script for Neovim integration.

This script tests the core functionality of the Neovim integration
without relying on the full API infrastructure.
"""

import os
import sys
import asyncio
import time
import json
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with patch('agent.tools.neovim_tool.requests') as mock_requests:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_requests.post.return_value = mock_response
    mock_requests.get.return_value = mock_response
    mock_requests.get.return_value = mock_response
    
    from agent.tools.neovim_tool import neovim_tool
    from agent.tools.parallel_workflow import parallel_workflow_manager
    from agent.tools.workflow_integration import workflow_integration


async def test_neovim_tool():
    """Test the Neovim tool functionality."""
    print("Testing Neovim tool...")
    
    instance_id = f"test_instance_{int(time.time())}"
    success = await neovim_tool.start_instance(instance_id)
    
    if not success:
        print("❌ Failed to start Neovim instance")
        return False
    
    print("✅ Started Neovim instance")
    
    command = ":echo 'Hello from Neovim'<CR>"
    result = await neovim_tool.execute_command(
        instance_id,
        command,
        background=False
    )
    
    if "error" in result:
        print(f"❌ Failed to execute Neovim command: {result['error']}")
        return False
    
    print("✅ Executed Neovim command")
    
    plugin_command = ":lua require('tmux').resize_direction('h', 10)<CR>"
    plugin_result = await neovim_tool.execute_command(
        instance_id,
        plugin_command,
        plugin="tmux"
    )
    
    if "error" in plugin_result:
        print(f"❌ Failed to execute plugin command: {plugin_result['error']}")
        return False
    
    print("✅ Executed plugin command")
    
    stop_success = await neovim_tool.stop_instance(instance_id)
    
    if not stop_success:
        print("❌ Failed to stop Neovim instance")
        return False
    
    print("✅ Stopped Neovim instance")
    
    return True


async def test_parallel_workflow():
    """Test the parallel workflow functionality."""
    print("\nTesting parallel workflow...")
    
    instance_id = f"test_instance_{int(time.time())}"
    await neovim_tool.start_instance(instance_id)
    
    workflow_id = f"test_workflow_{int(time.time())}"
    workflow_result = await parallel_workflow_manager.create_workflow(
        workflow_id,
        instance_id,
        "Test workflow",
        {"test": True}
    )
    
    if "error" in workflow_result:
        print(f"❌ Failed to create workflow: {workflow_result['error']}")
        return False
    
    print("✅ Created workflow")
    
    task_id = f"test_task_{int(time.time())}"
    task_result = await parallel_workflow_manager.register_task(
        workflow_id,
        task_id,
        "neovim",
        instance_id,
        ":echo 'Hello'<CR>",
        {"test": True}
    )
    
    if "error" in task_result:
        print(f"❌ Failed to register task: {task_result['error']}")
        return False
    
    print("✅ Registered task")
    
    execute_result = await parallel_workflow_manager.execute_task(
        task_id
    )
    
    if "error" in execute_result:
        print(f"❌ Failed to execute task: {execute_result['error']}")
        return False
    
    print("✅ Executed task")
    
    tasks_result = await parallel_workflow_manager.get_workflow_tasks(
        workflow_id
    )
    
    if "error" in tasks_result:
        print(f"❌ Failed to get workflow tasks: {tasks_result['error']}")
        return False
    
    print("✅ Retrieved workflow tasks")
    
    await neovim_tool.stop_instance(instance_id)
    
    return True


async def test_workflow_integration():
    """Test the workflow integration functionality."""
    print("\nTesting workflow integration...")
    
    instance_id = f"test_instance_{int(time.time())}"
    await neovim_tool.start_instance(instance_id)
    
    workflow_id = f"test_workflow_{int(time.time())}"
    integration_id = f"test_integration_{int(time.time())}"
    
    integration_result = await workflow_integration.create_integration(
        integration_id,
        instance_id,
        workflow_id,
        "Test integration",
        {"test": True}
    )
    
    if "error" in integration_result:
        print(f"❌ Failed to create integration: {integration_result['error']}")
        return False
    
    print("✅ Created integration")
    
    mapping_result = await workflow_integration.register_state_mapping(
        integration_id,
        "current_file",
        "active_file",
        True
    )
    
    if "error" in mapping_result:
        print(f"❌ Failed to register state mapping: {mapping_result['error']}")
        return False
    
    print("✅ Registered state mapping")
    
    parallel_result = await workflow_integration.execute_parallel_command(
        integration_id,
        ":e test.py<CR>",
        "Open test.py in IDE",
        file="test.py"
    )
    
    if "error" in parallel_result:
        print(f"❌ Failed to execute parallel command: {parallel_result['error']}")
        return False
    
    print("✅ Executed parallel command")
    
    status_result = await workflow_integration.get_integration_status(
        integration_id
    )
    
    if "error" in status_result:
        print(f"❌ Failed to get integration status: {status_result['error']}")
        return False
    
    print("✅ Retrieved integration status")
    
    await neovim_tool.stop_instance(instance_id)
    
    return True


async def test_plugin_support():
    """Test the plugin support functionality."""
    print("\nTesting plugin support...")
    
    instance_id = f"plugin_test_{int(time.time())}"
    success = await neovim_tool.start_instance(instance_id)
    
    if not success:
        print("❌ Failed to start Neovim instance")
        return False
    
    print("✅ Started Neovim instance for plugin testing")
    
    tmux_result = await neovim_tool.execute_command(
        instance_id,
        ":lua require('tmux').resize_direction('h', 10)<CR>",
        plugin="tmux"
    )
    
    if "error" in tmux_result:
        print(f"❌ Failed to execute tmux command: {tmux_result['error']}")
        return False
    
    print("✅ Tested tmux.nvim plugin")
    
    fzf_result = await neovim_tool.execute_command(
        instance_id,
        ":lua require('fzf-lua').files()<CR>",
        plugin="fzf"
    )
    
    if "error" in fzf_result:
        print(f"❌ Failed to execute fzf command: {fzf_result['error']}")
        return False
    
    print("✅ Tested fzf-lua plugin")
    
    markdown_result = await neovim_tool.execute_command(
        instance_id,
        ":MarkdownPreview<CR>",
        file="README.md",
        plugin="markdown"
    )
    
    if "error" in markdown_result:
        print(f"❌ Failed to execute markdown command: {markdown_result['error']}")
        return False
    
    print("✅ Tested markdown-preview.nvim plugin")
    
    ts_result = await neovim_tool.execute_command(
        instance_id,
        ":CocCommand tsserver.goToDefinition<CR>",
        file="test.ts",
        plugin="coc"
    )
    
    if "error" in ts_result:
        print(f"❌ Failed to execute TypeScript command: {ts_result['error']}")
        return False
    
    print("✅ Tested coc-tsserver plugin")
    
    await neovim_tool.stop_instance(instance_id)
    
    return True


async def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("Running Neovim Integration Tests")
    print("=" * 80)
    
    neovim_tool_success = await test_neovim_tool()
    parallel_workflow_success = await test_parallel_workflow()
    workflow_integration_success = await test_workflow_integration()
    plugin_support_success = await test_plugin_support()
    
    print("\n" + "=" * 80)
    print("Test Results:")
    print(f"Neovim Tool: {'✅ PASS' if neovim_tool_success else '❌ FAIL'}")
    print(f"Parallel Workflow: {'✅ PASS' if parallel_workflow_success else '❌ FAIL'}")
    print(f"Workflow Integration: {'✅ PASS' if workflow_integration_success else '❌ FAIL'}")
    print(f"Plugin Support: {'✅ PASS' if plugin_support_success else '❌ FAIL'}")
    print("=" * 80)
    
    return (
        neovim_tool_success and
        parallel_workflow_success and
        workflow_integration_success and
        plugin_support_success
    )


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
