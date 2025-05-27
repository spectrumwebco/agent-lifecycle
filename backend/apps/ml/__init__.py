"""
RLLM integration for python_ml.

This package provides integration of the RLLM framework for reinforcement
learning of language models with the existing ML infrastructure.
"""

from .config.rllm_config import (
    RLLMConfig,
    RLLMModelConfig,
    RLLMTrainingConfig,
    RLLMDistributedConfig,
    RLLMRewardConfig,
    get_deepcoder_config,
)
from .models.rllm_model import RLLMModel, RLLMModelManager
from .rewards.issue_rewards import (
    IssueRewardFunction,
    CodeQualityReward,
    ComprehensiveExplanationReward,
    SolutionAccuracyReward,
    RewardCalculator,
)
from .data.trajectory_dataset import (
    RLLMTrajectoryExample,
    RLLMTrajectoryDataset,
    TrajectoryConverter,
)
from .training.trainer import RLLMTrainer
from .training.distributed import DistributedTrainer
from .integration.ml_integration import MLIntegration
from .integration.benchmark_integration import BenchmarkIntegration
from .integration.trajectory_integration import TrajectoryIntegration
from .integration.agent_integration import AgentIntegration

__all__ = [
    "RLLMConfig",
    "RLLMModelConfig",
    "RLLMTrainingConfig",
    "RLLMDistributedConfig",
    "RLLMRewardConfig",
    "get_deepcoder_config",
    "RLLMModel",
    "RLLMModelManager",
    "IssueRewardFunction",
    "CodeQualityReward",
    "ComprehensiveExplanationReward",
    "SolutionAccuracyReward",
    "RewardCalculator",
    "RLLMTrajectoryExample",
    "RLLMTrajectoryDataset",
    "TrajectoryConverter",
    "RLLMTrainer",
    "DistributedTrainer",
    "MLIntegration",
    "BenchmarkIntegration",
    "TrajectoryIntegration",
    "AgentIntegration",
]
