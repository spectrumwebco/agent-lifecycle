"""
Neovim agent for the Python agent.

This module provides a Neovim agent that can be used as a secondary interface
for the Python agent, allowing it to perform operations in parallel with the
primary IDE.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union

from .neovim_integration import NeovimIntegration

logger = logging.getLogger(__name__)

class NeovimAgent:
    """
    Neovim agent for the Python agent.
    
    This class provides a Neovim agent that can be used as a secondary interface
    for the Python agent, allowing it to perform operations in parallel with the
    primary IDE.
    """
    
    def __init__(self, container_type: str = "kata", container_name: str = "default"):
        """
        Initialize the Neovim agent.
        
        Args:
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
        """
        self.container_type = container_type
        self.container_name = container_name
        self.neovim = NeovimIntegration(container_type, container_name)
        self.state = {
            "status": "initialized",
            "current_file": None,
            "current_directory": None,
            "tmux_sessions": [],
            "terminals": [],
            "plugins": [],
        }
        
    async def start(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Start the Neovim agent.
        
        Args:
            options: Options for starting the Neovim agent
            
        Returns:
            True if the Neovim agent was started successfully, False otherwise
        """
        logger.info(f"Starting Neovim agent for {self.container_type} container: {self.container_name}")
        
        if options is None:
            options = {}
            
        if not self.neovim.launch(options):
            logger.error("Failed to launch Neovim")
            return False
            
        self.state["status"] = "running"
        
        self.state["current_directory"] = os.getcwd()
        
        return True
    
    async def stop(self) -> bool:
        """
        Stop the Neovim agent.
        
        Returns:
            True if the Neovim agent was stopped successfully, False otherwise
        """
        logger.info(f"Stopping Neovim agent for {self.container_type} container: {self.container_name}")
        
        if not self.neovim.stop():
            logger.error("Failed to stop Neovim")
            return False
            
        self.state["status"] = "stopped"
        
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the Neovim agent.
        
        Returns:
            The status of the Neovim agent
        """
        logger.info(f"Getting status of Neovim agent for {self.container_type} container: {self.container_name}")
        
        neovim_status = self.neovim.get_status()
        
        if neovim_status.get("status") == "running":
            self.state["status"] = "running"
        else:
            self.state["status"] = "stopped"
            
        return {
            "neovim": neovim_status,
            "agent": self.state,
        }
    
    async def open_file(self, file_path: str) -> bool:
        """
        Open a file in the Neovim agent.
        
        Args:
            file_path: The path to the file to open
            
        Returns:
            True if the file was opened successfully, False otherwise
        """
        logger.info(f"Opening file in Neovim agent: {file_path}")
        
        if not self.neovim.open_file(file_path):
            logger.error(f"Failed to open file in Neovim: {file_path}")
            return False
            
        self.state["current_file"] = file_path
        
        return True
    
    async def run_terminal_command(self, command: str) -> bool:
        """
        Run a terminal command in the Neovim agent.
        
        Args:
            command: The command to run
            
        Returns:
            True if the command was run successfully, False otherwise
        """
        logger.info(f"Running terminal command in Neovim agent: {command}")
        
        if not self.neovim.run_terminal_command(command):
            logger.error(f"Failed to run terminal command in Neovim: {command}")
            return False
            
        self.state["terminals"].append(command)
        
        return True
    
    async def bulk_terminal_management(self, commands: List[str]) -> Dict[str, bool]:
        """
        Run multiple terminal commands in the Neovim agent.
        
        Args:
            commands: The commands to run
            
        Returns:
            A dictionary mapping commands to their success status
        """
        logger.info(f"Running multiple terminal commands in Neovim agent")
        
        results = self.neovim.bulk_terminal_management(commands)
        
        for command, success in results.items():
            if success:
                self.state["terminals"].append(command)
                
        return results
    
    async def create_tmux_session(self, session_name: str, window_name: str = "main") -> bool:
        """
        Create a tmux session in the Neovim agent.
        
        Args:
            session_name: The name of the tmux session
            window_name: The name of the tmux window
            
        Returns:
            True if the tmux session was created successfully, False otherwise
        """
        logger.info(f"Creating tmux session in Neovim agent: {session_name}")
        
        if not self.neovim.create_tmux_session(session_name, window_name):
            logger.error(f"Failed to create tmux session in Neovim: {session_name}")
            return False
            
        self.state["tmux_sessions"].append(session_name)
        
        return True
    
    async def attach_to_tmux_session(self, session_name: str) -> bool:
        """
        Attach to a tmux session in the Neovim agent.
        
        Args:
            session_name: The name of the tmux session
            
        Returns:
            True if the tmux session was attached to successfully, False otherwise
        """
        logger.info(f"Attaching to tmux session in Neovim agent: {session_name}")
        
        if not self.neovim.attach_to_tmux_session(session_name):
            logger.error(f"Failed to attach to tmux session in Neovim: {session_name}")
            return False
            
        return True
    
    async def install_plugin(self, name: str, repo: str) -> bool:
        """
        Install a plugin in the Neovim agent.
        
        Args:
            name: The name of the plugin
            repo: The repository URL of the plugin
            
        Returns:
            True if the plugin was installed successfully, False otherwise
        """
        logger.info(f"Installing plugin in Neovim agent: {name} from {repo}")
        
        if not self.neovim.install_plugin(name, repo):
            logger.error(f"Failed to install plugin in Neovim: {name} from {repo}")
            return False
            
        self.state["plugins"].append({"name": name, "repo": repo})
        
        return True
    
    async def execute_command(self, command: str) -> bool:
        """
        Execute a command in the Neovim agent.
        
        Args:
            command: The command to execute
            
        Returns:
            True if the command was executed successfully, False otherwise
        """
        logger.info(f"Executing command in Neovim agent: {command}")
        
        if not self.neovim.execute_command(command):
            logger.error(f"Failed to execute command in Neovim: {command}")
            return False
            
        return True
