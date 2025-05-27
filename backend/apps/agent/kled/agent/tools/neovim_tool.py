"""
Neovim tool for the Python agent that allows interacting with Neovim as a
parallel workflow with state persistence integration.
"""

import asyncio
import os
from typing import Dict, Any, Optional, List, Tuple
import requests

from ..utils.log import get_logger

# Try to import the database integration
try:
    from ...tools.neovim.db_integration import neovim_db_integration
except ImportError:
    neovim_db_integration = None

# Try to import the shared state integration
try:
    from ...integrations.neovim_state import neovim_state_manager
except ImportError:
    neovim_state_manager = None


class NeovimTool:
    """Tool for interacting with Neovim as a parallel workflow environment with state persistence."""

    def __init__(self):
        """Initialize the Neovim tool."""
        self.logger = get_logger("neovim-tool", emoji="📝")
        self.neovim_api_base = os.environ.get("NEOVIM_API_BASE", "http://localhost:8090/neovim")
        self.active_instances = {}
        self.background_tasks = {}
        
        self.db_integration_enabled = neovim_db_integration is not None
        self.shared_state_enabled = neovim_state_manager is not None
        
        if self.shared_state_enabled and neovim_state_manager is not None:
            neovim_state_manager.start()

    async def start_instance(self, instance_id: str) -> bool:
        """Start a new Neovim instance.

        Args:
            instance_id: Unique identifier for the Neovim instance

        Returns:
            bool: True if instance was started successfully
        """
        try:
            response = requests.post(
                f"{self.neovim_api_base}/start",
                json={"id": instance_id},
                timeout=10
            )
            if response.status_code == 200:
                self.active_instances[instance_id] = True
                self.logger.info("Started Neovim instance: %s", instance_id)
                
                if self.db_integration_enabled and neovim_db_integration is not None:
                    try:
                        await neovim_db_integration.start_sync(instance_id, self.neovim_api_base)
                        await neovim_db_integration.restore_state(instance_id, self.neovim_api_base)
                    except Exception as db_error:
                        self.logger.warning("Database integration error: %s", db_error)
                
                if self.shared_state_enabled and neovim_state_manager is not None:
                    try:
                        neovim_state_manager.start_sync(instance_id, self.neovim_api_base)
                        neovim_state_manager.restore_instance_state(instance_id, self.neovim_api_base)
                    except Exception as state_error:
                        self.logger.warning("Shared state integration error: %s", state_error)
                
                return True
            
            self.logger.error("Failed to start Neovim instance: %s", response.text)
            return False
        except Exception as e:
            self.logger.error("Error starting Neovim instance: %s", e)
            return False

    async def stop_instance(self, instance_id: str) -> bool:
        """Stop a Neovim instance.

        Args:
            instance_id: Unique identifier for the Neovim instance

        Returns:
            bool: True if instance was stopped successfully
        """
        try:
            if self.db_integration_enabled and neovim_db_integration is not None:
                try:
                    await neovim_db_integration.stop_sync(instance_id)
                except Exception as db_error:
                    self.logger.warning("Database integration error during stop: %s", db_error)
            
            if self.shared_state_enabled and neovim_state_manager is not None:
                try:
                    neovim_state_manager.stop_sync(instance_id)
                except Exception as state_error:
                    self.logger.warning("Shared state integration error during stop: %s", state_error)
            
            response = requests.post(
                f"{self.neovim_api_base}/stop",
                json={"id": instance_id},
                timeout=10
            )
            if response.status_code == 200:
                if instance_id in self.active_instances:
                    del self.active_instances[instance_id]
                self.logger.info("Stopped Neovim instance: %s", instance_id)
                return True
            
            self.logger.error("Failed to stop Neovim instance: %s", response.text)
            return False
        except Exception as e:
            self.logger.error("Error stopping Neovim instance: %s", e)
            return False

    async def execute_command(
        self,
        instance_id: str,
        command: str,
        file: Optional[str] = None,
        background: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Execute a command in a Neovim instance.

        Args:
            instance_id: Unique identifier for the Neovim instance
            command: Neovim command to execute
            file: Optional file to open before executing the command
            background: Whether to run in background (parallel)

        Returns:
            Optional[Dict[str, Any]]: Command result or None if running in
            background
        """
        if instance_id not in self.active_instances:
            success = await self.start_instance(instance_id)
            if not success:
                return {"error": "Failed to start Neovim instance"}

        if file:
            file_open_result = await self._execute_command(
                instance_id, f":e {file}<CR>"
            )
            if "error" in file_open_result:
                return file_open_result

        if background:
            task = asyncio.create_task(
                self._execute_command(instance_id, command)
            )
            task_id = f"{instance_id}_{len(self.background_tasks)}"
            self.background_tasks[task_id] = task
            self.logger.info(
                "Started background task %s for Neovim instance: %s",
                task_id, instance_id
            )
            return {"status": "running_in_background", "task_id": task_id}
        
        return await self._execute_command(instance_id, command)

    async def _execute_command(
        self, instance_id: str, command: str
    ) -> Dict[str, Any]:
        """Internal method to execute a command.

        Args:
            instance_id: Unique identifier for the Neovim instance
            command: Neovim command to execute

        Returns:
            Dict[str, Any]: Command result
        """
        try:
            response = requests.post(
                f"{self.neovim_api_base}/execute",
                json={"id": instance_id, "command": command},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            
            self.logger.error("Failed to execute Neovim command: %s", response.text)
            return {"error": f"Failed to execute command: {response.text}"}
        except Exception as e:
            self.logger.error("Error executing Neovim command: %s", e)
            return {"error": f"Error executing command: {str(e)}"}

    async def get_state(self, instance_id: str) -> Dict[str, Any]:
        """Get the current state of a Neovim instance.

        Args:
            instance_id: Unique identifier for the Neovim instance

        Returns:
            Dict[str, Any]: Current state
        """
        try:
            response = requests.get(
                f"{self.neovim_api_base}/state",
                params={"id": instance_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            
            self.logger.error("Failed to get Neovim state: %s", response.text)
            return {"error": f"Failed to get state: {response.text}"}
        except Exception as e:
            self.logger.error("Error getting Neovim state: %s", e)
            return {"error": f"Error getting state: {str(e)}"}

    async def get_background_tasks(self) -> List[str]:
        """Get a list of all background tasks.

        Returns:
            List[str]: List of task IDs
        """
        return list(self.background_tasks.keys())

    async def check_background_task(self, task_id: str) -> Dict[str, Any]:
        """Check the status of a background task.

        Args:
            task_id: ID of the background task

        Returns:
            Dict[str, Any]: Task status
        """
        if task_id not in self.background_tasks:
            return {"error": f"No background task with ID {task_id}"}

        task = self.background_tasks[task_id]
        if task.done():
            try:
                result = task.result()
                del self.background_tasks[task_id]
                return {"status": "completed", "result": result}
            except Exception as e:
                del self.background_tasks[task_id]
                return {"status": "failed", "error": str(e)}
        
        return {"status": "running"}

    async def cancel_background_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a background task.

        Args:
            task_id: ID of the background task

        Returns:
            Dict[str, Any]: Cancellation result
        """
        if task_id not in self.background_tasks:
            return {"error": f"No background task with ID {task_id}"}

        task = self.background_tasks[task_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        del self.background_tasks[task_id]
        return {"status": "cancelled"}

    async def start_bulk_instances(self, count: int, prefix: str = "neovim_") -> List[str]:
        """Start multiple Neovim instances in bulk.

        Args:
            count: Number of instances to start
            prefix: Prefix for instance IDs

        Returns:
            List[str]: List of started instance IDs
        """
        instance_ids = []
        for i in range(count):
            instance_id = f"{prefix}{i}"
            success = await self.start_instance(instance_id)
            if success:
                instance_ids.append(instance_id)
        
        self.logger.info("Started %d Neovim instances in bulk", len(instance_ids))
        return instance_ids

    async def execute_in_all(self, command: str, file: Optional[str] = None) -> Dict[str, Any]:
        """Execute a command in all active Neovim instances.

        Args:
            command: Neovim command to execute
            file: Optional file to open before executing the command

        Returns:
            Dict[str, Any]: Results for each instance
        """
        results = {}
        for instance_id in list(self.active_instances.keys()):
            results[instance_id] = await self.execute_command(
                instance_id, command, file=file
            )
        
        return results

    async def execute_agent_framework_command(
        self, 
        instance_id: str, 
        command: str, 
        terminal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command through the agent_framework terminal integration.

        Args:
            instance_id: Unique identifier for the Neovim instance
            command: Shell command to execute
            terminal_id: Optional terminal ID for the agent_framework

        Returns:
            Dict[str, Any]: Command result
        """
        if not terminal_id:
            terminal_id = f"neovim_{instance_id}"
        
        neovim_command = f":terminal {command}<CR>"
        
        result = await self.execute_command(instance_id, neovim_command)
        if result is None:
            return {"error": "Failed to execute command in Neovim instance"}
        
        try:
            self.logger.info(
                "Registered terminal command with agent_framework: %s (terminal: %s)",
                command, terminal_id
            )
        except Exception as e:
            self.logger.error("Failed to register with agent_framework: %s", e)
        
        return result

    async def cleanup(self) -> None:
        """Clean up all Neovim instances and background tasks."""
        for task_id, task in list(self.background_tasks.items()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.background_tasks[task_id]

        for instance_id in list(self.active_instances.keys()):
            await self.stop_instance(instance_id)
        
        if self.db_integration_enabled and neovim_db_integration is not None:
            try:
                await neovim_db_integration.cleanup()
            except Exception as db_error:
                self.logger.warning("Database integration cleanup error: %s", db_error)
        
        if self.shared_state_enabled and neovim_state_manager is not None:
            try:
                neovim_state_manager.stop()
            except Exception as state_error:
                self.logger.warning("Shared state integration cleanup error: %s", state_error)

        self.logger.info("Cleaned up all Neovim instances and background tasks")


neovim_tool = NeovimTool()
