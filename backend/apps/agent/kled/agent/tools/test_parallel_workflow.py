"""
Test script for parallel workflow capabilities in Neovim integration.

This script tests the parallel workflow capabilities of the Neovim integration
by executing commands in Neovim while performing operations in the IDE.
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional

from .neovim_tool import neovim_tool
from .parallel_workflow import parallel_workflow_manager
from .workflow_integration import workflow_integration
from ..utils.log import get_logger


async def test_parallel_workflow():
    """Test the parallel workflow capabilities."""
    logger = get_logger("test-parallel-workflow", emoji="🧪")
    logger.info("Starting parallel workflow test")
    
    instance_id = f"test_instance_{int(time.time())}"
    success = await neovim_tool.start_instance(instance_id)
    
    if not success:
        logger.error("Failed to start Neovim instance")
        return False
    
    logger.info(f"Started Neovim instance: {instance_id}")
    
    workflow_id = f"test_workflow_{int(time.time())}"
    workflow_result = await parallel_workflow_manager.create_workflow(
        workflow_id,
        instance_id,
        "Test workflow",
        {"test": True}
    )
    
    if "error" in workflow_result:
        logger.error(f"Failed to create workflow: {workflow_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Created workflow: {workflow_id}")
    
    integration_id = f"test_integration_{int(time.time())}"
    integration_result = await workflow_integration.create_integration(
        integration_id,
        instance_id,
        workflow_id,
        "Test integration",
        {"test": True}
    )
    
    if "error" in integration_result:
        logger.error(f"Failed to create integration: {integration_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Created integration: {integration_id}")
    
    await workflow_integration.register_state_mapping(
        integration_id,
        "current_file",
        "active_file",
        True
    )
    
    await workflow_integration.register_state_mapping(
        integration_id,
        "current_mode",
        "editor_mode",
        True
    )
    
    neovim_result = await neovim_tool.execute_command(
        instance_id,
        ":echo 'Hello from Neovim'<CR>",
        background=False
    )
    
    if "error" in neovim_result:
        logger.error(f"Failed to execute Neovim command: {neovim_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Executed Neovim command: {neovim_result}")
    
    parallel_result = await workflow_integration.execute_parallel_command(
        integration_id,
        ":e test.py<CR>iprint('Hello, world!')<ESC>:w<CR>",
        "Open test.py in IDE",
        file="test.py",
        plugin="coc",
        sync_after=True
    )
    
    if "error" in parallel_result:
        logger.error(f"Failed to execute parallel commands: {parallel_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Executed parallel commands: {parallel_result}")
    
    await asyncio.sleep(2)
    
    status_result = await workflow_integration.get_integration_status(
        integration_id
    )
    
    if "error" in status_result:
        logger.error(f"Failed to get integration status: {status_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Integration status: {json.dumps(status_result, indent=2)}")
    
    await neovim_tool.stop_instance(instance_id)
    
    logger.info("Parallel workflow test completed successfully")
    return True


async def test_plugin_integration():
    """Test the plugin integration capabilities."""
    logger = get_logger("test-plugin-integration", emoji="🔌")
    logger.info("Starting plugin integration test")
    
    instance_id = f"plugin_test_{int(time.time())}"
    success = await neovim_tool.start_instance(instance_id)
    
    if not success:
        logger.error("Failed to start Neovim instance")
        return False
    
    logger.info(f"Started Neovim instance: {instance_id}")
    
    tmux_result = await neovim_tool.execute_command(
        instance_id,
        ":lua require('tmux').resize_direction('h', 10)<CR>",
        plugin="tmux"
    )
    
    if "error" in tmux_result:
        logger.error(f"Failed to execute tmux command: {tmux_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Executed tmux command: {tmux_result}")
    
    fzf_result = await neovim_tool.execute_command(
        instance_id,
        ":lua require('fzf-lua').files()<CR>",
        plugin="fzf"
    )
    
    if "error" in fzf_result:
        logger.error(f"Failed to execute fzf command: {fzf_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Executed fzf command: {fzf_result}")
    
    markdown_result = await neovim_tool.execute_command(
        instance_id,
        ":MarkdownPreview<CR>",
        file="README.md",
        plugin="markdown"
    )
    
    if "error" in markdown_result:
        logger.error(f"Failed to execute markdown command: {markdown_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Executed markdown command: {markdown_result}")
    
    ts_result = await neovim_tool.execute_command(
        instance_id,
        ":CocCommand tsserver.goToDefinition<CR>",
        file="test.ts",
        plugin="coc"
    )
    
    if "error" in ts_result:
        logger.error(f"Failed to execute TypeScript command: {ts_result['error']}")
        await neovim_tool.stop_instance(instance_id)
        return False
    
    logger.info(f"Executed TypeScript command: {ts_result}")
    
    await neovim_tool.stop_instance(instance_id)
    
    logger.info("Plugin integration test completed successfully")
    return True


async def run_tests():
    """Run all tests."""
    logger = get_logger("neovim-tests", emoji="🧪")
    logger.info("Starting Neovim integration tests")
    
    workflow_success = await test_parallel_workflow()
    
    plugin_success = await test_plugin_integration()
    
    if workflow_success and plugin_success:
        logger.info("All tests passed successfully")
        return True
    else:
        logger.error("Some tests failed")
        return False


if __name__ == "__main__":
    asyncio.run(run_tests())
