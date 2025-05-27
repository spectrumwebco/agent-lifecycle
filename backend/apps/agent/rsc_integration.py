"""
Integration module for React Server Components (RSC) with Django.
This module provides functionality for generating and managing React Server Components
based on agent actions and tool usage.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from django.conf import settings

from .go_integration import get_go_runtime_integration

logger = logging.getLogger(__name__)

class RSCIntegration:
    """
    Integration class for React Server Components (RSC) with Django.
    """
    
    def __init__(self):
        """
        Initialize the RSC integration.
        """
        self.go_runtime = get_go_runtime_integration()
        self.component_cache = {}
    
    def generate_component(self, component_type: str, props: Dict[str, Any]) -> str:
        """
        Generate a React Server Component.
        
        Args:
            component_type: Type of the component to generate
            props: Properties for the component
            
        Returns:
            Component ID
        """
        try:
            result = self.go_runtime.execute_task(
                task_type="generate_component",
                input_data={
                    "component_type": component_type,
                    "props": props
                },
                description=f"Generate {component_type} component"
            )
            
            if "error" in result:
                logger.error(f"Error generating component: {result['error']}")
                return None
            
            component_id = result.get("component_id")
            if component_id:
                self.component_cache[component_id] = result.get("component", {})
            
            return component_id
        except Exception as e:
            logger.error(f"Error generating component: {e}")
            return None
    
    def generate_component_from_agent_action(
        self, 
        agent_id: str, 
        action_id: str, 
        action_type: str, 
        action_data: Dict[str, Any]
    ) -> str:
        """
        Generate a React Server Component from an agent action.
        
        Args:
            agent_id: ID of the agent
            action_id: ID of the action
            action_type: Type of the action
            action_data: Data for the action
            
        Returns:
            Component ID
        """
        try:
            result = self.go_runtime.execute_task(
                task_type="generate_component_from_agent_action",
                input_data={
                    "agent_id": agent_id,
                    "action_id": action_id,
                    "action_type": action_type,
                    "action_data": action_data
                },
                description=f"Generate component for {action_type} action"
            )
            
            if "error" in result:
                logger.error(f"Error generating component from agent action: {result['error']}")
                return None
            
            component_id = result.get("component_id")
            if component_id:
                self.component_cache[component_id] = result.get("component", {})
            
            return component_id
        except Exception as e:
            logger.error(f"Error generating component from agent action: {e}")
            return None
    
    def generate_component_from_tool_usage(
        self, 
        agent_id: str, 
        tool_id: str, 
        tool_name: str, 
        tool_input: Dict[str, Any], 
        tool_output: Dict[str, Any]
    ) -> str:
        """
        Generate a React Server Component from a tool usage.
        
        Args:
            agent_id: ID of the agent
            tool_id: ID of the tool
            tool_name: Name of the tool
            tool_input: Input data for the tool
            tool_output: Output data from the tool
            
        Returns:
            Component ID
        """
        try:
            result = self.go_runtime.execute_task(
                task_type="generate_component_from_tool_usage",
                input_data={
                    "agent_id": agent_id,
                    "tool_id": tool_id,
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_output": tool_output
                },
                description=f"Generate component for {tool_name} tool usage"
            )
            
            if "error" in result:
                logger.error(f"Error generating component from tool usage: {result['error']}")
                return None
            
            component_id = result.get("component_id")
            if component_id:
                self.component_cache[component_id] = result.get("component", {})
            
            return component_id
        except Exception as e:
            logger.error(f"Error generating component from tool usage: {e}")
            return None
    
    def get_component(self, component_id: str) -> Dict[str, Any]:
        """
        Get a component by ID.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Component data
        """
        if component_id in self.component_cache:
            return self.component_cache[component_id]
        
        try:
            result = self.go_runtime.execute_task(
                task_type="get_component",
                input_data={
                    "component_id": component_id
                },
                description=f"Get component {component_id}"
            )
            
            if "error" in result:
                logger.error(f"Error getting component: {result['error']}")
                return None
            
            component = result.get("component", {})
            if component:
                self.component_cache[component_id] = component
            
            return component
        except Exception as e:
            logger.error(f"Error getting component: {e}")
            return None
    
    def list_components(self) -> List[Dict[str, Any]]:
        """
        List all components.
        
        Returns:
            List of components
        """
        try:
            result = self.go_runtime.execute_task(
                task_type="list_components",
                input_data={},
                description="List all components"
            )
            
            if "error" in result:
                logger.error(f"Error listing components: {result['error']}")
                return []
            
            components = result.get("components", [])
            
            for component in components:
                if "id" in component:
                    self.component_cache[component["id"]] = component
            
            return components
        except Exception as e:
            logger.error(f"Error listing components: {e}")
            return []
    
    def get_components_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all components for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of components
        """
        try:
            result = self.go_runtime.execute_task(
                task_type="get_components_by_agent",
                input_data={
                    "agent_id": agent_id
                },
                description=f"Get components for agent {agent_id}"
            )
            
            if "error" in result:
                logger.error(f"Error getting components by agent: {result['error']}")
                return []
            
            components = result.get("components", [])
            
            for component in components:
                if "id" in component:
                    self.component_cache[component["id"]] = component
            
            return components
        except Exception as e:
            logger.error(f"Error getting components by agent: {e}")
            return []
    
    def get_components_by_tool(self, tool_id: str) -> List[Dict[str, Any]]:
        """
        Get all components for a tool.
        
        Args:
            tool_id: ID of the tool
            
        Returns:
            List of components
        """
        try:
            result = self.go_runtime.execute_task(
                task_type="get_components_by_tool",
                input_data={
                    "tool_id": tool_id
                },
                description=f"Get components for tool {tool_id}"
            )
            
            if "error" in result:
                logger.error(f"Error getting components by tool: {result['error']}")
                return []
            
            components = result.get("components", [])
            
            for component in components:
                if "id" in component:
                    self.component_cache[component["id"]] = component
            
            return components
        except Exception as e:
            logger.error(f"Error getting components by tool: {e}")
            return []

_rsc_integration = None

def get_rsc_integration() -> RSCIntegration:
    """
    Get the RSC integration singleton instance.
    
    Returns:
        RSC integration instance
    """
    global _rsc_integration
    if _rsc_integration is None:
        _rsc_integration = RSCIntegration()
    return _rsc_integration
