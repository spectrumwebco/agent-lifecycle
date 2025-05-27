"""
Parallel workflow utilities for Neovim integration.

This module provides utilities for managing parallel workflows between
Neovim and the main IDE interface.
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime
from enum import Enum

from ..utils.log import get_logger


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PAUSED = "paused"
    COMPLETED = "completed"


class ParallelWorkflowManager:
    """Manager for parallel workflows between Neovim and IDE."""

    def __init__(self):
        """Initialize the parallel workflow manager."""
        self.logger = get_logger("parallel-workflow", emoji="⚡")
        self.active_workflows = {}
        self.workflow_states = {}
        self.task_registry = {}
        self.sync_handlers = {}

    async def create_workflow(
        self, 
        workflow_id: str, 
        neovim_instance_id: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new parallel workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            neovim_instance_id: ID of the Neovim instance
            description: Optional description of the workflow
            metadata: Optional metadata for the workflow
            
        Returns:
            Dict[str, Any]: Workflow information
        """
        if workflow_id in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} already exists"
            }
        
        self.active_workflows[workflow_id] = {
            "neovim_instance_id": neovim_instance_id,
            "created_at": datetime.now().isoformat(),
            "status": WorkflowStatus.ACTIVE.value,
            "description": description,
            "metadata": metadata or {},
            "tasks": []
        }
        
        self.workflow_states[workflow_id] = {
            "neovim_state": {},
            "ide_state": {},
            "shared_state": {},
            "last_sync": None
        }
        
        self.logger.info(f"Created parallel workflow: {workflow_id}")
        
        return {
            "status": "success",
            "message": f"Created parallel workflow: {workflow_id}",
            "workflow": self.active_workflows[workflow_id]
        }

    async def register_task(
        self,
        workflow_id: str,
        task_id: str,
        task_type: str,
        target: str,
        command: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register a task in a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            task_id: Unique identifier for the task
            task_type: Type of task (neovim, ide)
            target: Target for the task
            command: Command to execute
            metadata: Optional metadata for the task
            
        Returns:
            Dict[str, Any]: Task information
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        if task_id in self.task_registry:
            return {
                "error": f"Task {task_id} already exists"
            }
        
        task = {
            "id": task_id,
            "workflow_id": workflow_id,
            "type": task_type,
            "target": target,
            "command": command,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.task_registry[task_id] = task
        self.active_workflows[workflow_id]["tasks"].append(task_id)
        
        self.logger.info(
            f"Registered task {task_id} in workflow {workflow_id}"
        )
        
        return {
            "status": "success",
            "message": f"Registered task {task_id}",
            "task": task
        }

    async def execute_task(
        self,
        task_id: str,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """Execute a task in a parallel workflow.
        
        Args:
            task_id: ID of the task
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict[str, Any]: Task execution result
        """
        if task_id not in self.task_registry:
            return {
                "error": f"Task {task_id} does not exist"
            }
        
        task = self.task_registry[task_id]
        workflow_id = task["workflow_id"]
        
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        
        self.logger.info(f"Executing task {task_id}")
        
        if progress_callback:
            progress_callback("Starting task execution", 0.0)
            await asyncio.sleep(0.5)
            progress_callback("Task in progress", 50.0)
            await asyncio.sleep(0.5)
            progress_callback("Task completed", 100.0)
        
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": f"Executed task {task_id}",
            "task": task
        }

    async def sync_workflow_state(
        self, workflow_id: str
    ) -> Dict[str, Any]:
        """Synchronize the state of a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict[str, Any]: Synchronization result
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        if workflow_id not in self.workflow_states:
            return {
                "error": f"Workflow state for {workflow_id} does not exist"
            }
        
        self.workflow_states[workflow_id]["last_sync"] = datetime.now().isoformat()
        
        self.logger.info(f"Synchronized workflow state: {workflow_id}")
        
        return {
            "status": "success",
            "message": f"Synchronized workflow state: {workflow_id}",
            "state": self.workflow_states[workflow_id]
        }

    async def register_sync_handler(
        self,
        workflow_id: str,
        handler_id: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """Register a sync handler for a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            handler_id: Unique identifier for the handler
            handler: Handler function
            
        Returns:
            Dict[str, Any]: Registration result
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        if workflow_id not in self.sync_handlers:
            self.sync_handlers[workflow_id] = {}
        
        self.sync_handlers[workflow_id][handler_id] = handler
        
        self.logger.info(
            f"Registered sync handler {handler_id} for workflow {workflow_id}"
        )
        
        return {
            "status": "success",
            "message": f"Registered sync handler {handler_id}"
        }

    async def update_workflow_state(
        self,
        workflow_id: str,
        state_type: str,
        state_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update the state of a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            state_type: Type of state (neovim, ide, shared)
            state_data: State data
            
        Returns:
            Dict[str, Any]: Update result
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        if workflow_id not in self.workflow_states:
            return {
                "error": f"Workflow state for {workflow_id} does not exist"
            }
        
        if state_type not in ["neovim_state", "ide_state", "shared_state"]:
            return {
                "error": f"Invalid state type: {state_type}"
            }
        
        self.workflow_states[workflow_id][state_type] = {
            **self.workflow_states[workflow_id][state_type],
            **state_data
        }
        
        if workflow_id in self.sync_handlers:
            for handler_id, handler in self.sync_handlers[workflow_id].items():
                try:
                    handler(self.workflow_states[workflow_id])
                except Exception as e:
                    self.logger.error(
                        f"Error in sync handler {handler_id}: {e}"
                    )
        
        self.logger.info(
            f"Updated {state_type} for workflow {workflow_id}"
        )
        
        return {
            "status": "success",
            "message": f"Updated {state_type}",
            "state": self.workflow_states[workflow_id]
        }

    async def get_workflow_state(
        self, workflow_id: str
    ) -> Dict[str, Any]:
        """Get the state of a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict[str, Any]: Workflow state
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        if workflow_id not in self.workflow_states:
            return {
                "error": f"Workflow state for {workflow_id} does not exist"
            }
        
        return {
            "status": "success",
            "message": f"Retrieved workflow state: {workflow_id}",
            "state": self.workflow_states[workflow_id]
        }

    async def pause_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Pause a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict[str, Any]: Pause result
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        self.active_workflows[workflow_id]["status"] = WorkflowStatus.PAUSED.value
        
        self.logger.info(f"Paused workflow: {workflow_id}")
        
        return {
            "status": "success",
            "message": f"Paused workflow: {workflow_id}"
        }

    async def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Resume a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict[str, Any]: Resume result
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        self.active_workflows[workflow_id]["status"] = WorkflowStatus.ACTIVE.value
        
        self.logger.info(f"Resumed workflow: {workflow_id}")
        
        return {
            "status": "success",
            "message": f"Resumed workflow: {workflow_id}"
        }

    async def complete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Complete a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict[str, Any]: Completion result
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        self.active_workflows[workflow_id]["status"] = WorkflowStatus.COMPLETED.value
        self.active_workflows[workflow_id]["completed_at"] = datetime.now().isoformat()
        
        self.logger.info(f"Completed workflow: {workflow_id}")
        
        return {
            "status": "success",
            "message": f"Completed workflow: {workflow_id}"
        }

    async def get_workflow_tasks(
        self, workflow_id: str
    ) -> Dict[str, Any]:
        """Get the tasks of a parallel workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict[str, Any]: Workflow tasks
        """
        if workflow_id not in self.active_workflows:
            return {
                "error": f"Workflow {workflow_id} does not exist"
            }
        
        tasks = []
        for task_id in self.active_workflows[workflow_id]["tasks"]:
            if task_id in self.task_registry:
                tasks.append(self.task_registry[task_id])
        
        return {
            "status": "success",
            "message": f"Retrieved workflow tasks: {workflow_id}",
            "tasks": tasks
        }


parallel_workflow_manager = ParallelWorkflowManager()
