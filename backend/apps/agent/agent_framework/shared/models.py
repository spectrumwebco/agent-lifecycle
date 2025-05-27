"""
Shared models for agent framework.

This module provides shared models that can be used by both Kled and Veigar agents.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Agent configuration model."""
    
    class ModelConfig(BaseModel):
        """Model configuration."""
        model_name: str = "gemini-2.5-pro"
        temperature: float = 0.0
        top_p: float = 1.0
        per_instance_cost_limit: float = 3.0
    
    class ToolConfig(BaseModel):
        """Tool configuration."""
        name: str
        description: str
        module: str
        class_name: str
        parameters: Dict[str, Dict[str, Any]]
    
    model: ModelConfig = Field(default_factory=ModelConfig)
    prompt_template: str
    max_iterations: int = 10
    tools: List[ToolConfig] = Field(default_factory=list)


class EnvironmentConfig(BaseModel):
    """Environment configuration model."""
    
    class RepoConfig(BaseModel):
        """Repository configuration."""
        repo_url: str
        branch: str
        pr_id: Optional[str] = None
        commit_hash: Optional[str] = None
    
    repo: Optional[RepoConfig] = None
    working_directory: Optional[str] = None
    environment_variables: Dict[str, str] = Field(default_factory=dict)


class ProblemStatement(BaseModel):
    """Problem statement model."""
    
    title: str
    description: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    additional_context: Dict[str, Any] = Field(default_factory=dict)


class TrajectoryStep(BaseModel):
    """Trajectory step model."""
    
    role: str
    content: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Trajectory(BaseModel):
    """Trajectory model."""
    
    steps: List[TrajectoryStep] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_step(self, step: TrajectoryStep) -> None:
        """Add a step to the trajectory."""
        self.steps.append(step)
    
    def get_steps_by_role(self, role: str) -> List[TrajectoryStep]:
        """Get all steps with the given role."""
        return [step for step in self.steps if step.role == role]
    
    def get_last_step(self) -> Optional[TrajectoryStep]:
        """Get the last step in the trajectory."""
        if not self.steps:
            return None
        return self.steps[-1]
    
    def get_last_step_by_role(self, role: str) -> Optional[TrajectoryStep]:
        """Get the last step with the given role."""
        steps = self.get_steps_by_role(role)
        if not steps:
            return None
        return steps[-1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the trajectory to a dictionary."""
        return {
            "steps": [step.dict() for step in self.steps],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trajectory":
        """Create a trajectory from a dictionary."""
        steps = [TrajectoryStep(**step) for step in data.get("steps", [])]
        metadata = data.get("metadata", {})
        return cls(steps=steps, metadata=metadata)


class AgentResult(BaseModel):
    """Agent result model."""
    
    trajectory: Trajectory
    info: Dict[str, Any] = Field(default_factory=dict)
