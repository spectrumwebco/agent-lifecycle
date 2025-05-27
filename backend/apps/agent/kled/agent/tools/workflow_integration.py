"""
Workflow integration module for connecting Neovim and IDE workflows.

This module provides integration between the parallel workflow manager and
the Neovim tool, enabling seamless transitions between the two environments.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime

from ..utils.log import get_logger
from .neovim_tool import neovim_tool
from .parallel_workflow import parallel_workflow_manager


class WorkflowIntegration:
    """Integration between Neovim and IDE workflows."""

    def __init__(self):
        """Initialize the workflow integration."""
        self.logger = get_logger("workflow-integration", emoji="🔄")
        self.active_integrations = {}
        self.state_mappings = {}
        self.event_handlers = {}

    async def create_integration(
        self,
        integration_id: str,
        neovim_instance_id: str,
        workflow_id: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new workflow integration.
        
        Args:
            integration_id: Unique identifier for the integration
            neovim_instance_id: ID of the Neovim instance
            workflow_id: ID of the parallel workflow
            description: Optional description of the integration
            metadata: Optional metadata for the integration
            
        Returns:
            Dict[str, Any]: Integration information
        """
        if integration_id in self.active_integrations:
            return {
                "error": f"Integration {integration_id} already exists"
            }
        
        workflow_result = await parallel_workflow_manager.create_workflow(
            workflow_id,
            neovim_instance_id,
            description,
            metadata
        )
        
        if "error" in workflow_result:
            return workflow_result
        
        self.active_integrations[integration_id] = {
            "neovim_instance_id": neovim_instance_id,
            "workflow_id": workflow_id,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "metadata": metadata or {},
            "status": "active"
        }
        
        self.state_mappings[integration_id] = {
            "neovim_to_workflow": {},
            "workflow_to_neovim": {}
        }
        
        await parallel_workflow_manager.register_sync_handler(
            workflow_id,
            f"neovim_sync_{integration_id}",
            self._handle_workflow_state_change
        )
        
        self.logger.info(f"Created workflow integration: {integration_id}")
        
        return {
            "status": "success",
            "message": f"Created workflow integration: {integration_id}",
            "integration": self.active_integrations[integration_id]
        }

    async def _handle_workflow_state_change(
        self, state: Dict[str, Any]
    ) -> None:
        """Handle workflow state changes.
        
        Args:
            state: Updated workflow state
        """
        integration_id = None
        for id, integration in self.active_integrations.items():
            if integration["workflow_id"] == state.get("workflow_id"):
                integration_id = id
                break
        
        if not integration_id:
            return
        
        if integration_id in self.state_mappings:
            mappings = self.state_mappings[integration_id]["workflow_to_neovim"]
            neovim_instance_id = self.active_integrations[integration_id]["neovim_instance_id"]
            
            for workflow_key, neovim_key in mappings.items():
                if workflow_key in state.get("shared_state", {}):
                    value = state["shared_state"][workflow_key]
                    await self._update_neovim_state(
                        neovim_instance_id, neovim_key, value
                    )
        
        if integration_id in self.event_handlers:
            for handler_id, handler in self.event_handlers[integration_id].items():
                try:
                    handler(state)
                except Exception as e:
                    self.logger.error(
                        f"Error in event handler {handler_id}: {e}"
                    )

    async def _update_neovim_state(
        self, instance_id: str, key: str, value: Any
    ) -> None:
        """Update Neovim state.
        
        Args:
            instance_id: ID of the Neovim instance
            key: State key
            value: State value
        """
        self.logger.info(
            f"Updating Neovim state for instance {instance_id}: "
            f"{key} = {value}"
        )

    async def register_state_mapping(
        self,
        integration_id: str,
        neovim_key: str,
        workflow_key: str,
        bidirectional: bool = True
    ) -> Dict[str, Any]:
        """Register a state mapping between Neovim and workflow.
        
        Args:
            integration_id: ID of the integration
            neovim_key: Key in Neovim state
            workflow_key: Key in workflow state
            bidirectional: Whether the mapping is bidirectional
            
        Returns:
            Dict[str, Any]: Registration result
        """
        if integration_id not in self.active_integrations:
            return {
                "error": f"Integration {integration_id} does not exist"
            }
        
        self.state_mappings[integration_id]["neovim_to_workflow"][neovim_key] = workflow_key
        
        if bidirectional:
            self.state_mappings[integration_id]["workflow_to_neovim"][workflow_key] = neovim_key
        
        self.logger.info(
            f"Registered state mapping for integration {integration_id}: "
            f"{neovim_key} <-> {workflow_key}"
        )
        
        return {
            "status": "success",
            "message": f"Registered state mapping: {neovim_key} <-> {workflow_key}"
        }

    async def register_event_handler(
        self,
        integration_id: str,
        handler_id: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """Register an event handler for an integration.
        
        Args:
            integration_id: ID of the integration
            handler_id: Unique identifier for the handler
            handler: Handler function
            
        Returns:
            Dict[str, Any]: Registration result
        """
        if integration_id not in self.active_integrations:
            return {
                "error": f"Integration {integration_id} does not exist"
            }
        
        if integration_id not in self.event_handlers:
            self.event_handlers[integration_id] = {}
        
        self.event_handlers[integration_id][handler_id] = handler
        
        self.logger.info(
            f"Registered event handler {handler_id} for integration {integration_id}"
        )
        
        return {
            "status": "success",
            "message": f"Registered event handler {handler_id}"
        }

    async def sync_states(
        self, integration_id: str
    ) -> Dict[str, Any]:
        """Synchronize states between Neovim and workflow.
        
        Args:
            integration_id: ID of the integration
            
        Returns:
            Dict[str, Any]: Synchronization result
        """
        if integration_id not in self.active_integrations:
            return {
                "error": f"Integration {integration_id} does not exist"
            }
        
        neovim_instance_id = self.active_integrations[integration_id]["neovim_instance_id"]
        workflow_id = self.active_integrations[integration_id]["workflow_id"]
        
        neovim_state_result = await neovim_tool.get_state(
            neovim_instance_id, refresh=True
        )
        
        if "error" in neovim_state_result:
            return neovim_state_result
        
        workflow_state_result = await parallel_workflow_manager.get_workflow_state(
            workflow_id
        )
        
        if "error" in workflow_state_result:
            return workflow_state_result
        
        if integration_id in self.state_mappings:
            mappings = self.state_mappings[integration_id]["neovim_to_workflow"]
            
            updates = {}
            for neovim_key, workflow_key in mappings.items():
                if "data" in neovim_state_result and neovim_key in neovim_state_result["data"]:
                    updates[workflow_key] = neovim_state_result["data"][neovim_key]
            
            if updates:
                await parallel_workflow_manager.update_workflow_state(
                    workflow_id, "shared_state", updates
                )
        
        if integration_id in self.state_mappings:
            mappings = self.state_mappings[integration_id]["workflow_to_neovim"]
            
            for workflow_key, neovim_key in mappings.items():
                if "state" in workflow_state_result and "shared_state" in workflow_state_result["state"]:
                    if workflow_key in workflow_state_result["state"]["shared_state"]:
                        value = workflow_state_result["state"]["shared_state"][workflow_key]
                        await self._update_neovim_state(
                            neovim_instance_id, neovim_key, value
                        )
        
        self.logger.info(f"Synchronized states for integration {integration_id}")
        
        return {
            "status": "success",
            "message": f"Synchronized states for integration {integration_id}"
        }

    async def execute_parallel_command(
        self,
        integration_id: str,
        neovim_command: str,
        ide_command: Optional[str] = None,
        file: Optional[str] = None,
        plugin: Optional[str] = None,
        sync_after: bool = True
    ) -> Dict[str, Any]:
        """Execute commands in parallel in Neovim and IDE.
        
        Args:
            integration_id: ID of the integration
            neovim_command: Command to execute in Neovim
            ide_command: Optional command to execute in IDE
            file: Optional file to open before executing the command
            plugin: Optional plugin to use for the Neovim command
            sync_after: Whether to synchronize states after execution
            
        Returns:
            Dict[str, Any]: Execution result
        """
        if integration_id not in self.active_integrations:
            return {
                "error": f"Integration {integration_id} does not exist"
            }
        
        neovim_instance_id = self.active_integrations[integration_id]["neovim_instance_id"]
        workflow_id = self.active_integrations[integration_id]["workflow_id"]
        
        neovim_result = await neovim_tool.execute_command(
            neovim_instance_id,
            neovim_command,
            file=file,
            background=True,
            plugin=plugin
        )
        
        if "task_id" in neovim_result:
            await parallel_workflow_manager.register_task(
                workflow_id,
                neovim_result["task_id"],
                "neovim",
                neovim_instance_id,
                neovim_command,
                {
                    "file": file,
                    "plugin": plugin
                }
            )
        
        ide_result = None
        if ide_command:
            self.logger.info(f"Executing IDE command: {ide_command}")
            
            ide_task_id = f"ide_{workflow_id}_{datetime.now().timestamp()}"
            await parallel_workflow_manager.register_task(
                workflow_id,
                ide_task_id,
                "ide",
                "ide",
                ide_command,
                {
                    "file": file
                }
            )
            
            ide_result = {
                "status": "success",
                "message": f"Executed IDE command: {ide_command}",
                "task_id": ide_task_id
            }
        
        if sync_after:
            await self.sync_states(integration_id)
        
        return {
            "status": "success",
            "message": f"Executed parallel commands for integration {integration_id}",
            "neovim_result": neovim_result,
            "ide_result": ide_result
        }

    async def get_integration_status(
        self, integration_id: str
    ) -> Dict[str, Any]:
        """Get the status of an integration.
        
        Args:
            integration_id: ID of the integration
            
        Returns:
            Dict[str, Any]: Integration status
        """
        if integration_id not in self.active_integrations:
            return {
                "error": f"Integration {integration_id} does not exist"
            }
        
        neovim_instance_id = self.active_integrations[integration_id]["neovim_instance_id"]
        workflow_id = self.active_integrations[integration_id]["workflow_id"]
        
        neovim_state_result = await neovim_tool.get_state(
            neovim_instance_id
        )
        
        workflow_tasks_result = await parallel_workflow_manager.get_workflow_tasks(
            workflow_id
        )
        
        return {
            "status": "success",
            "message": f"Retrieved integration status: {integration_id}",
            "integration": self.active_integrations[integration_id],
            "neovim_state": neovim_state_result.get("data", {}),
            "workflow_tasks": workflow_tasks_result.get("tasks", [])
        }


workflow_integration = WorkflowIntegration()
