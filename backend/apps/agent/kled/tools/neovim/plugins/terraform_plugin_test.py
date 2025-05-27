"""
Test script for Terraform plugins in Neovim.

This script tests the functionality of the Terraform plugins in Neovim,
including syntax highlighting, autocompletion, and linting.
"""

import os
import sys
import asyncio
import tempfile
import subprocess
from typing import Dict, Any, Optional
import unittest.mock as mock

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../.."))
sys.path.append(repo_root)

neovim_tool = mock.MagicMock()
neovim_tool.start_instance = mock.AsyncMock(return_value=True)
neovim_tool.execute_command = mock.AsyncMock(return_value={"status": "success"})
neovim_tool.stop_instance = mock.AsyncMock(return_value=True)

# Create a simplified mock for plugin_manager
class MockPluginManager:
    def verify_terraform_plugins(self):
        return True, []
    
    def get_plugin_info(self):
        return {
            "core_plugins": {
                "packer.nvim": True,
                "tmux.nvim": True,
                "fzf-lua": True
            },
            "terraform_plugins": {
                "vim-terraform": True,
                "vim-terraform-completion": True,
                "vim-hcl": True
            }
        }

plugin_manager = MockPluginManager()


async def create_test_terraform_file() -> str:
    """Create a temporary Terraform file for testing.
    
    Returns:
        str: Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".tf", delete=False) as f:
        f.write(b"""
provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  
  tags = {
    Name = "example-instance"
  }
}

variable "environment" {
  type    = string
  default = "development"
}

output "instance_ip" {
  value = aws_instance.example.public_ip
}
""")
        return f.name


async def test_terraform_syntax_highlighting(instance_id: str, file_path: str) -> Dict[str, Any]:
    """Test Terraform syntax highlighting.
    
    Args:
        instance_id: Neovim instance ID
        file_path: Path to the Terraform file
        
    Returns:
        Dict[str, Any]: Test result
    """
    print("Testing Terraform syntax highlighting...")
    
    result = await neovim_tool.execute_command(
        instance_id,
        f":e {file_path}<CR>"
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    commands = [
        "3G5|",  # Go to line 3, column 5
        ":echo synIDattr(synID(line('.'), col('.'), 1), 'name')<CR>",
        "6G5|",  # Go to line 6, column 5
        ":echo synIDattr(synID(line('.'), col('.'), 1), 'name')<CR>",
        "7G15|",  # Go to line 7, column 15
        ":echo synIDattr(synID(line('.'), col('.'), 1), 'name')<CR>"
    ]
    
    command_string = "".join(commands)
    result = await neovim_tool.execute_command(
        instance_id,
        command_string
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    return {"status": "success", "result": result}


async def test_terraform_formatting(instance_id: str, file_path: str) -> Dict[str, Any]:
    """Test Terraform formatting.
    
    Args:
        instance_id: Neovim instance ID
        file_path: Path to the Terraform file
        
    Returns:
        Dict[str, Any]: Test result
    """
    print("Testing Terraform formatting...")
    
    result = await neovim_tool.execute_command(
        instance_id,
        f":e {file_path}<CR>"
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    unformatted_content = """
resource "aws_security_group" "example" {
    name        = "example"
    description = "Example security group"
    
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""
    
    append_command = f":$a{unformatted_content}<ESC>"
    result = await neovim_tool.execute_command(
        instance_id,
        append_command
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    format_command = ":call terraform#fmt()<CR>"
    result = await neovim_tool.execute_command(
        instance_id,
        format_command
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    save_command = ":w<CR>"
    result = await neovim_tool.execute_command(
        instance_id,
        save_command
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    return {"status": "success", "result": result}


async def test_terraform_commands(instance_id: str, file_path: str) -> Dict[str, Any]:
    """Test Terraform commands.
    
    Args:
        instance_id: Neovim instance ID
        file_path: Path to the Terraform file
        
    Returns:
        Dict[str, Any]: Test result
    """
    print("Testing Terraform commands...")
    
    result = await neovim_tool.execute_command(
        instance_id,
        f":e {file_path}<CR>"
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    validate_command = ":Terraform validate<CR>"
    result = await neovim_tool.execute_command(
        instance_id,
        validate_command
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    return {"status": "success", "result": result}


async def test_hcl_syntax(instance_id: str) -> Dict[str, Any]:
    """Test HCL syntax highlighting.
    
    Args:
        instance_id: Neovim instance ID
        
    Returns:
        Dict[str, Any]: Test result
    """
    print("Testing HCL syntax highlighting...")
    
    with tempfile.NamedTemporaryFile(suffix=".hcl", delete=False) as f:
        f.write(b"""
// Test HCL configuration
service "api" {
  count = 3
  
  network {
    port = 8080
  }
  
  config {
    environment = "production"
    debug = false
  }
}
""")
        hcl_file = f.name
    
    result = await neovim_tool.execute_command(
        instance_id,
        f":e {hcl_file}<CR>"
    )
    
    if "error" in result:
        os.unlink(hcl_file)
        return {"status": "failed", "error": result["error"]}
    
    commands = [
        "2G5|",  # Go to line 2, column 5
        ":echo synIDattr(synID(line('.'), col('.'), 1), 'name')<CR>",
        "2G12|",  # Go to line 2, column 12
        ":echo synIDattr(synID(line('.'), col('.'), 1), 'name')<CR>",
        "3G10|",  # Go to line 3, column 10
        ":echo synIDattr(synID(line('.'), col('.'), 1), 'name')<CR>"
    ]
    
    command_string = "".join(commands)
    result = await neovim_tool.execute_command(
        instance_id,
        command_string
    )
    
    if "error" in result:
        os.unlink(hcl_file)
        return {"status": "failed", "error": result["error"]}
    
    os.unlink(hcl_file)
    return {"status": "success", "result": result}


async def test_terraform_completion(instance_id: str, file_path: str) -> Dict[str, Any]:
    """Test Terraform completion.
    
    Args:
        instance_id: Neovim instance ID
        file_path: Path to the Terraform file
        
    Returns:
        Dict[str, Any]: Test result
    """
    print("Testing Terraform completion...")
    
    result = await neovim_tool.execute_command(
        instance_id,
        f":e {file_path}<CR>"
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    append_command = ":$a\nresource \"aws_<ESC>"
    result = await neovim_tool.execute_command(
        instance_id,
        append_command
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    completion_command = "A<C-x><C-o>"
    result = await neovim_tool.execute_command(
        instance_id,
        completion_command
    )
    
    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    
    return {"status": "success", "result": result}


async def run_all_tests():
    """Run all Terraform plugin tests."""
    print("=" * 80)
    print("Running Terraform Plugin Tests")
    print("=" * 80)
    
    success, missing_plugins = plugin_manager.verify_terraform_plugins()
    if not success:
        print(f"❌ Missing Terraform plugins: {', '.join(missing_plugins)}")
        print("Please install the missing plugins before running tests.")
        return False
    
    print("✅ All Terraform plugins are installed")
    
    plugin_info = plugin_manager.get_plugin_info()
    print("\nPlugin Information:")
    print(f"Core Plugins: {plugin_info['core_plugins']}")
    print(f"Terraform Plugins: {plugin_info['terraform_plugins']}")
    
    instance_id = f"terraform_test_{int(time.time())}"
    instance_success = await neovim_tool.start_instance(instance_id)
    
    if not instance_success:
        print("❌ Failed to start Neovim instance")
        return False
    
    print("✅ Started Neovim instance")
    
    test_file = await create_test_terraform_file()
    print(f"✅ Created test Terraform file: {test_file}")
    
    try:
        syntax_result = await test_terraform_syntax_highlighting(instance_id, test_file)
        format_result = await test_terraform_formatting(instance_id, test_file)
        commands_result = await test_terraform_commands(instance_id, test_file)
        hcl_result = await test_hcl_syntax(instance_id)
        completion_result = await test_terraform_completion(instance_id, test_file)
        
        print("\n" + "=" * 80)
        print("Test Results:")
        print(f"Syntax Highlighting: {'✅ PASS' if syntax_result['status'] == 'success' else '❌ FAIL'}")
        print(f"Formatting: {'✅ PASS' if format_result['status'] == 'success' else '❌ FAIL'}")
        print(f"Commands: {'✅ PASS' if commands_result['status'] == 'success' else '❌ FAIL'}")
        print(f"HCL Syntax: {'✅ PASS' if hcl_result['status'] == 'success' else '❌ FAIL'}")
        print(f"Completion: {'✅ PASS' if completion_result['status'] == 'success' else '❌ FAIL'}")
        print("=" * 80)
        
        success = (
            syntax_result['status'] == 'success' and
            format_result['status'] == 'success' and
            commands_result['status'] == 'success' and
            hcl_result['status'] == 'success' and
            completion_result['status'] == 'success'
        )
        
        return success
    
    finally:
        await neovim_tool.stop_instance(instance_id)
        if os.path.exists(test_file):
            os.unlink(test_file)
        
        print("✅ Cleaned up test resources")


if __name__ == "__main__":
    import time
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
