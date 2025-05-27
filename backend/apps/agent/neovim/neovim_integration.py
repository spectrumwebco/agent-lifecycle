"""
Neovim integration for the Python agent.

This module provides integration between the Python agent and Neovim,
allowing the agent to use Neovim as a secondary interface for development.
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)

class NeovimIntegration:
    """
    Integration between the Python agent and Neovim.
    
    This class provides methods for the Python agent to interact with Neovim,
    allowing it to use Neovim as a secondary interface for development.
    """
    
    def __init__(self, container_type: str = "kata", container_name: str = "default"):
        """
        Initialize the Neovim integration.
        
        Args:
            container_type: The type of container to use (kata, sysbox, kind)
            container_name: The name of the container to use
        """
        self.container_type = container_type
        self.container_name = container_name
        self.socket_path = self._get_socket_path()
        self.is_running = False
        
    def _get_socket_path(self) -> str:
        """
        Get the path to the Neovim socket.
        
        Returns:
            The path to the Neovim socket
        """
        home_dir = os.path.expanduser("~")
        return os.path.join(
            home_dir, 
            ".local", 
            "share", 
            "nvim", 
            self.container_type, 
            self.container_name, 
            "neovim.sock"
        )
    
    def launch(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Launch Neovim.
        
        Args:
            options: Options for launching Neovim
            
        Returns:
            True if Neovim was launched successfully, False otherwise
        """
        logger.info(f"Launching Neovim for {self.container_type} container: {self.container_name}")
        
        if options is None:
            options = {}
            
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "launch",
                "--container-type", self.container_type,
                "--container-name", self.container_name
            ]
            
            for key, value in options.items():
                cmd.extend([f"--{key}", str(value)])
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to launch Neovim: {result.stderr}")
                return False
                
            self.is_running = True
            return True
        except Exception as e:
            logger.error(f"Error launching Neovim: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop Neovim.
        
        Returns:
            True if Neovim was stopped successfully, False otherwise
        """
        logger.info(f"Stopping Neovim for {self.container_type} container: {self.container_name}")
        
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "stop",
                "--container-type", self.container_type,
                "--container-name", self.container_name
            ]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to stop Neovim: {result.stderr}")
                return False
                
            self.is_running = False
            return True
        except Exception as e:
            logger.error(f"Error stopping Neovim: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of Neovim.
        
        Returns:
            The status of Neovim
        """
        logger.info(f"Getting status of Neovim for {self.container_type} container: {self.container_name}")
        
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "status",
                "--container-type", self.container_type,
                "--container-name", self.container_name
            ]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to get Neovim status: {result.stderr}")
                return {"status": "error", "message": result.stderr}
                
            try:
                status = json.loads(result.stdout)
                self.is_running = status.get("status") == "running"
                return status
            except json.JSONDecodeError:
                return {"status": "unknown", "output": result.stdout}
        except Exception as e:
            logger.error(f"Error getting Neovim status: {e}")
            return {"status": "error", "message": str(e)}
    
    def execute_command(self, command: str) -> bool:
        """
        Execute a command in Neovim.
        
        Args:
            command: The command to execute
            
        Returns:
            True if the command was executed successfully, False otherwise
        """
        logger.info(f"Executing command in Neovim: {command}")
        
        if not self.is_running:
            logger.error("Neovim is not running")
            return False
        
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "exec",
                "--container-type", self.container_type,
                "--container-name", self.container_name,
                "--command", command
            ]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to execute command in Neovim: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error executing command in Neovim: {e}")
            return False
    
    def open_file(self, file_path: str) -> bool:
        """
        Open a file in Neovim.
        
        Args:
            file_path: The path to the file to open
            
        Returns:
            True if the file was opened successfully, False otherwise
        """
        logger.info(f"Opening file in Neovim: {file_path}")
        
        if not self.is_running:
            logger.error("Neovim is not running")
            return False
        
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "exec",
                "--container-type", self.container_type,
                "--container-name", self.container_name,
                "--command", f":e {file_path}<CR>"
            ]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to open file in Neovim: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error opening file in Neovim: {e}")
            return False
    
    def run_terminal_command(self, command: str) -> bool:
        """
        Run a terminal command in Neovim.
        
        Args:
            command: The command to run
            
        Returns:
            True if the command was run successfully, False otherwise
        """
        logger.info(f"Running terminal command in Neovim: {command}")
        
        if not self.is_running:
            logger.error("Neovim is not running")
            return False
        
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "exec",
                "--container-type", self.container_type,
                "--container-name", self.container_name,
                "--command", f":terminal {command}<CR>"
            ]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to run terminal command in Neovim: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error running terminal command in Neovim: {e}")
            return False
    
    def install_plugin(self, name: str, repo: str) -> bool:
        """
        Install a plugin in Neovim.
        
        Args:
            name: The name of the plugin
            repo: The repository URL of the plugin
            
        Returns:
            True if the plugin was installed successfully, False otherwise
        """
        logger.info(f"Installing plugin in Neovim: {name} from {repo}")
        
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "install-plugin",
                "--container-type", self.container_type,
                "--container-name", self.container_name,
                "--plugin-name", name,
                "--plugin-repo", repo
            ]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to install plugin in Neovim: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error installing plugin in Neovim: {e}")
            return False
    
    def bulk_terminal_management(self, commands: List[str]) -> Dict[str, bool]:
        """
        Run multiple terminal commands in Neovim.
        
        Args:
            commands: The commands to run
            
        Returns:
            A dictionary mapping commands to their success status
        """
        logger.info(f"Running multiple terminal commands in Neovim")
        
        if not self.is_running:
            logger.error("Neovim is not running")
            return {cmd: False for cmd in commands}
        
        results = {}
        
        for command in commands:
            results[command] = self.run_terminal_command(command)
            
        return results
    
    def create_tmux_session(self, session_name: str, window_name: str = "main") -> bool:
        """
        Create a tmux session in Neovim.
        
        Args:
            session_name: The name of the tmux session
            window_name: The name of the tmux window
            
        Returns:
            True if the tmux session was created successfully, False otherwise
        """
        logger.info(f"Creating tmux session in Neovim: {session_name}")
        
        if not self.is_running:
            logger.error("Neovim is not running")
            return False
        
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "exec",
                "--container-type", self.container_type,
                "--container-name", self.container_name,
                "--command", f":terminal tmux new-session -s {session_name} -n {window_name}<CR>"
            ]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to create tmux session in Neovim: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error creating tmux session in Neovim: {e}")
            return False
    
    def attach_to_tmux_session(self, session_name: str) -> bool:
        """
        Attach to a tmux session in Neovim.
        
        Args:
            session_name: The name of the tmux session
            
        Returns:
            True if the tmux session was attached to successfully, False otherwise
        """
        logger.info(f"Attaching to tmux session in Neovim: {session_name}")
        
        if not self.is_running:
            logger.error("Neovim is not running")
            return False
        
        try:
            cmd = [
                "agent_runtime", 
                "neovim", 
                "exec",
                "--container-type", self.container_type,
                "--container-name", self.container_name,
                "--command", f":terminal tmux attach-session -t {session_name}<CR>"
            ]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to attach to tmux session in Neovim: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error attaching to tmux session in Neovim: {e}")
            return False
