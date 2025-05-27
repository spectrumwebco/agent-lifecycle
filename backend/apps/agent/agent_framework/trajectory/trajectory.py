"""
Trajectory tracking for the agent framework.

This module provides trajectory tracking capabilities for the agent framework,
allowing agents to record their execution steps.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class TrajectoryStep:
    """A step in a trajectory."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trajectory:
    """A trajectory of steps."""
    steps: List[TrajectoryStep] = field(default_factory=list)

    def add_step(self, step: TrajectoryStep) -> None:
        """Add a step to the trajectory."""
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the trajectory to a dictionary."""
        return {
            "steps": [
                {
                    "role": step.role,
                    "content": step.content,
                    **({"name": step.name} if step.name else {}),
                    **({"metadata": step.metadata} if step.metadata else {})
                }
                for step in self.steps
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trajectory":
        """Create a trajectory from a dictionary."""
        steps = [
            TrajectoryStep(
                role=step["role"],
                content=step["content"],
                name=step.get("name"),
                metadata=step.get("metadata", {})
            )
            for step in data.get("steps", [])
        ]
        return cls(steps=steps)
