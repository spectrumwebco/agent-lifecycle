"""
Neovim module for the Python agent.

This module provides Neovim integration for the Python agent, allowing it to
use Neovim as a secondary interface for development.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, cast

from ..neovim_agent import NeovimAgent
from ..agent_framework.base_module import BaseModule
from ..agent_framework.tool import Tool

logger = logging.getLogger(__name__)

class NeovimModule(BaseModule):
    """
    Neovim module for the Python agent.
    
    This module provides Neovim integration for the Python agent, allowing it to
    use Neovim as a secondary interface for development.
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """
        Initialize the Neovim module.
        
        Args:
            agent_config: The agent configuration
        """
        super().__init__(agent_config)
        self.name = "neovim"
        self.description = "Neovim integration for the Python agent"
        self.neovim_agents = {}
        self.default_container_type = agent_config.get("neovim", {}).get("default_container_type", "kata")
        self.default_container_name = agent_config.get("neovim", {}).get("default_container_name", "default")
        
    async def initialize(self) -> bool:
        """
        Initialize the Neovim module.
        
        Returns:
            True if the module was initialized successfully, False otherwise
        """
        logger.info("Initializing Neovim module")
        
        self.register_tools()
        
        await self.create_neovim_agent(self.default_container_type, self.default_container_name)
        
        return True
    
    async def cleanup(self) -> bool:
        """
        Clean up the Neovim module.
        
        Returns:
            True if the module was cleaned up successfully, False otherwise
        """
        logger.info("Cleaning up Neovim module")
        
        for agent_id, agent in self.neovim_agents.items():
            await agent.stop()
            
        return True
    
    def register_tools(self) -> None:
        """
        Register tools for the Neovim module.
        """
        self.register_tool(
            Tool(
                name="neovim_start",
                description="Start a Neovim agent",
                function=self.start_neovim_agent,
                parameters=[
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                    {
                        "name": "options",
                        "description": "Options for starting the Neovim agent",
                        "type": "object",
                        "required": False,
                        "default": {},
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_stop",
                description="Stop a Neovim agent",
                function=self.stop_neovim_agent,
                parameters=[
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_status",
                description="Get the status of a Neovim agent",
                function=self.get_neovim_agent_status,
                parameters=[
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_open_file",
                description="Open a file in a Neovim agent",
                function=self.open_file_in_neovim_agent,
                parameters=[
                    {
                        "name": "file_path",
                        "description": "The path to the file to open",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_run_terminal_command",
                description="Run a terminal command in a Neovim agent",
                function=self.run_terminal_command_in_neovim_agent,
                parameters=[
                    {
                        "name": "command",
                        "description": "The command to run",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_bulk_terminal_management",
                description="Run multiple terminal commands in a Neovim agent",
                function=self.bulk_terminal_management_in_neovim_agent,
                parameters=[
                    {
                        "name": "commands",
                        "description": "The commands to run",
                        "type": "array",
                        "required": True,
                    },
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_create_tmux_session",
                description="Create a tmux session in a Neovim agent",
                function=self.create_tmux_session_in_neovim_agent,
                parameters=[
                    {
                        "name": "session_name",
                        "description": "The name of the tmux session",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "window_name",
                        "description": "The name of the tmux window",
                        "type": "string",
                        "required": False,
                        "default": "main",
                    },
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_attach_to_tmux_session",
                description="Attach to a tmux session in a Neovim agent",
                function=self.attach_to_tmux_session_in_neovim_agent,
                parameters=[
                    {
                        "name": "session_name",
                        "description": "The name of the tmux session",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_install_plugin",
                description="Install a plugin in a Neovim agent",
                function=self.install_plugin_in_neovim_agent,
                parameters=[
                    {
                        "name": "name",
                        "description": "The name of the plugin",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "repo",
                        "description": "The repository URL of the plugin",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
        
        self.register_tool(
            Tool(
                name="neovim_execute_command",
                description="Execute a command in a Neovim agent",
                function=self.execute_command_in_neovim_agent,
                parameters=[
                    {
                        "name": "command",
                        "description": "The command to execute",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "container_type",
                        "description": "The type of container to use (kata, sysbox, kind)",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_type,
                    },
                    {
                        "name": "container_name",
                        "description": "The name of the container to use",
                        "type": "string",
                        "required": False,
                        "default": self.default_container_name,
                    },
                ],
            )
        )
    
    async def create_neovim_agent(self, container_type: Optional[str], container_name: Optional[str]) -> Optional[NeovimAgent]:
        """
        Create a Neovim agent.
        
        Args:
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The Neovim agent
        """
        logger.info(f"Creating Neovim agent for {container_type} container: {container_name}")
        
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent_id = f"{container_type}/{container_name}"
        
        if agent_id in self.neovim_agents:
            return self.neovim_agents[agent_id]
            
        agent = NeovimAgent(container_type, container_name)
        self.neovim_agents[agent_id] = agent
        
        return agent
    
    async def get_neovim_agent(self, container_type: Optional[str], container_name: Optional[str]) -> Optional[NeovimAgent]:
        """
        Get a Neovim agent.
        
        Args:
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The Neovim agent, or None if it doesn't exist
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent_id = f"{container_type}/{container_name}"
        
        if agent_id not in self.neovim_agents:
            return await self.create_neovim_agent(container_type, container_name)
            
        return self.neovim_agents[agent_id]
    
    async def start_neovim_agent(self, container_type: Optional[str] = None, container_name: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start a Neovim agent.
        
        Args:
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            options: Options for starting the Neovim agent
            
        Returns:
            The result of starting the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        if options is None:
            options = {}
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        if await agent.start(options):
            return {
                "success": True,
                "message": f"Neovim agent started for {container_type} container: {container_name}",
            }
        else:
            return {
                "success": False,
                "message": f"Failed to start Neovim agent for {container_type} container: {container_name}",
            }
    
    async def stop_neovim_agent(self, container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Stop a Neovim agent.
        
        Args:
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The result of stopping the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        if await agent.stop():
            return {
                "success": True,
                "message": f"Neovim agent stopped for {container_type} container: {container_name}",
            }
        else:
            return {
                "success": False,
                "message": f"Failed to stop Neovim agent for {container_type} container: {container_name}",
            }
    
    async def get_neovim_agent_status(self, container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the status of a Neovim agent.
        
        Args:
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The status of the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        return await agent.get_status()
    
    async def open_file_in_neovim_agent(self, file_path: str, container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Open a file in a Neovim agent.
        
        Args:
            file_path: The path to the file to open
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The result of opening the file in the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        if await agent.open_file(file_path):
            return {
                "success": True,
                "message": f"File opened in Neovim agent for {container_type} container: {container_name}",
                "file_path": file_path,
            }
        else:
            return {
                "success": False,
                "message": f"Failed to open file in Neovim agent for {container_type} container: {container_name}",
                "file_path": file_path,
            }
    
    async def run_terminal_command_in_neovim_agent(self, command: str, container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a terminal command in a Neovim agent.
        
        Args:
            command: The command to run
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The result of running the terminal command in the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        if await agent.run_terminal_command(command):
            return {
                "success": True,
                "message": f"Terminal command run in Neovim agent for {container_type} container: {container_name}",
                "command": command,
            }
        else:
            return {
                "success": False,
                "message": f"Failed to run terminal command in Neovim agent for {container_type} container: {container_name}",
                "command": command,
            }
    
    async def bulk_terminal_management_in_neovim_agent(self, commands: List[str], container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run multiple terminal commands in a Neovim agent.
        
        Args:
            commands: The commands to run
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The result of running multiple terminal commands in the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        results = await agent.bulk_terminal_management(commands)
        
        return {
            "success": True,
            "message": f"Multiple terminal commands run in Neovim agent for {container_type} container: {container_name}",
            "results": results,
        }
    
    async def create_tmux_session_in_neovim_agent(self, session_name: str, window_name: str = "main", container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a tmux session in a Neovim agent.
        
        Args:
            session_name: The name of the tmux session
            window_name: The name of the tmux window
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The result of creating a tmux session in the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        if await agent.create_tmux_session(session_name, window_name):
            return {
                "success": True,
                "message": f"Tmux session created in Neovim agent for {container_type} container: {container_name}",
                "session_name": session_name,
                "window_name": window_name,
            }
        else:
            return {
                "success": False,
                "message": f"Failed to create tmux session in Neovim agent for {container_type} container: {container_name}",
                "session_name": session_name,
                "window_name": window_name,
            }
    
    async def attach_to_tmux_session_in_neovim_agent(self, session_name: str, container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Attach to a tmux session in a Neovim agent.
        
        Args:
            session_name: The name of the tmux session
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The result of attaching to a tmux session in the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        if await agent.attach_to_tmux_session(session_name):
            return {
                "success": True,
                "message": f"Attached to tmux session in Neovim agent for {container_type} container: {container_name}",
                "session_name": session_name,
            }
        else:
            return {
                "success": False,
                "message": f"Failed to attach to tmux session in Neovim agent for {container_type} container: {container_name}",
                "session_name": session_name,
            }
    
    async def install_plugin_in_neovim_agent(self, name: str, repo: str, container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Install a plugin in a Neovim agent.
        
        Args:
            name: The name of the plugin
            repo: The repository URL of the plugin
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The result of installing a plugin in the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        if await agent.install_plugin(name, repo):
            return {
                "success": True,
                "message": f"Plugin installed in Neovim agent for {container_type} container: {container_name}",
                "name": name,
                "repo": repo,
            }
        else:
            return {
                "success": False,
                "message": f"Failed to install plugin in Neovim agent for {container_type} container: {container_name}",
                "name": name,
                "repo": repo,
            }
    
    async def execute_command_in_neovim_agent(self, command: str, container_type: Optional[str] = None, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a command in a Neovim agent.
        
        Args:
            command: The command to execute
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
            
        Returns:
            The result of executing a command in the Neovim agent
        """
        if container_type is None:
            container_type = self.default_container_type
            
        if container_name is None:
            container_name = self.default_container_name
            
        agent = await self.get_neovim_agent(container_type, container_name)
        
        if await agent.execute_command(command):
            return {
                "success": True,
                "message": f"Command executed in Neovim agent for {container_type} container: {container_name}",
                "command": command,
            }
        else:
            return {
                "success": False,
                "message": f"Failed to execute command in Neovim agent for {container_type} container: {container_name}",
                "command": command,
            }
