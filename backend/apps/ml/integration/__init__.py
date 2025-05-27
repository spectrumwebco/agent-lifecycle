"""
Integration with existing ML infrastructure.

This module provides integration between the RLLM framework and the
existing ML infrastructure, including trajectory generation, benchmarking,
and python_agent.
"""

from .ml_integration import MLIntegration
# from .benchmark_integration import BenchmarkIntegration
from .trajectory_integration import TrajectoryIntegration
from .agent_integration import AgentIntegration

__all__ = [
    "MLIntegration",
    # "BenchmarkIntegration",
    "TrajectoryIntegration",
    "AgentIntegration",
]
