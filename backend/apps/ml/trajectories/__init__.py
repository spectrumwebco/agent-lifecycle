"""
Trajectory generation module for AI Agent benchmarking.
"""

from .generator import TrajectoryStep, BenchmarkTrajectory

# TrajectoryGenerator is imported by other modules that need it directly
__all__ = ["TrajectoryStep", "BenchmarkTrajectory"]
