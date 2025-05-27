"""
Trajectory models for AI Agent benchmarking.

This module provides model classes for trajectory generation and benchmarking.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TrajectoryStep(BaseModel):
    """Single step in an agent trajectory."""

    action: str = Field(..., description="Action taken by the agent")
    observation: str = Field(..., description="Observation from the environment")
    response: str = Field(..., description="Agent's response to the observation")


class BenchmarkTrajectory(BaseModel):
    """Trajectory for benchmarking."""

    issue_id: str = Field(..., description="Issue ID")
    issue_url: str = Field(..., description="Issue URL")
    repository: str = Field(..., description="Repository name")
    steps: List[TrajectoryStep] = Field(
        default_factory=list, description="Trajectory steps"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Creation timestamp",
    )
    source: str = Field("github", description="Source of the issue (github or gitee)")
