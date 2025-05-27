"""
Tool for agent framework.

This module provides the Tool class for agent modules.
"""

from typing import Dict, List, Optional, Any, Callable


class Tool:
    """Tool for agent modules."""

    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize the tool.
        
        Args:
            name: The name of the tool
            description: The description of the tool
            function: The function to call when the tool is used
            parameters: The parameters for the tool
        """
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters or []
