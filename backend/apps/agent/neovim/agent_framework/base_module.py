"""
Base module for agent framework.

This module provides the base class for all agent modules.
"""

from typing import Dict, List, Optional, Any


class BaseModule:
    """Base class for all agent modules."""

    def __init__(self, agent_config: Dict[str, Any]):
        """
        Initialize the base module.
        
        Args:
            agent_config: The agent configuration
        """
        self.agent_config = agent_config
        self.name = "base"
        self.description = "Base module"
        self.tools = []
        
    async def initialize(self) -> bool:
        """
        Initialize the module.
        
        Returns:
            True if the module was initialized successfully, False otherwise
        """
        return True
    
    async def cleanup(self) -> bool:
        """
        Clean up the module.
        
        Returns:
            True if the module was cleaned up successfully, False otherwise
        """
        return True
    
    def register_tool(self, tool: Any) -> None:
        """
        Register a tool for the module.
        
        Args:
            tool: The tool to register
        """
        self.tools.append(tool)
