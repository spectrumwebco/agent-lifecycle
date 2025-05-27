"""
Shared runtime components for agent framework.

This module provides shared runtime components that can be used by both Kled and Veigar agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Literal, Annotated
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BaseModule(BaseModel):
    """Base module for agent framework modules."""
    
    @property
    def name(self) -> str:
        """Return the module name."""
        raise NotImplementedError("Module must implement name property")
    
    @property
    def description(self) -> str:
        """Return the module description."""
        raise NotImplementedError("Module must implement description property")
    
    @property
    def tools(self) -> List[Dict[str, Any]]:
        """Return a list of tools provided by the module."""
        raise NotImplementedError("Module must implement tools property")
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize the module with execution context."""
        raise NotImplementedError("Module must implement initialize method")
    
    def cleanup(self) -> bool:
        """Clean up module resources."""
        raise NotImplementedError("Module must implement cleanup method")


class RuntimeConfig(BaseModel):
    """Runtime configuration for agent framework."""
    
    model_name: str = "gemini-2.5-pro"
    temperature: float = 0.0
    top_p: float = 1.0
    cost_limit: float = 3.0
    max_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class AgentContext(BaseModel):
    """Agent context for agent framework."""
    
    agent_id: str
    agent_name: str
    agent_type: str
    runtime_config: RuntimeConfig = Field(default_factory=RuntimeConfig)
    modules: Dict[str, BaseModule] = Field(default_factory=dict)
    tools: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class AgentResult(BaseModel):
    """Agent result for agent framework."""
    
    status: str
    exit_status: Optional[str] = None
    submission: Optional[str] = None
    trajectory_id: Optional[str] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class AbstractRuntime(ABC):
    """Abstract runtime for agent framework.
    
    This is the main entry point for running agent operations.
    It provides an abstract interface that must be implemented by concrete runtimes.
    """

    def __init__(self, config: RuntimeConfig):
        """Initialize the runtime with configuration."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the runtime."""
        pass
    
    @abstractmethod
    def run_agent(self, config_obj: Any) -> Dict[str, Any]:
        """Run the agent with the specified configuration."""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up the runtime."""
        pass


class LocalRuntimeConfig(RuntimeConfig):
    """Local runtime configuration for agent framework."""
    
    environment: Dict[str, Any] = Field(default_factory=dict)
    working_directory: Optional[str] = None
