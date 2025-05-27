"""
Integration with benchmarking system.

This module provides integration between the RLLM framework and the
existing benchmarking infrastructure.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import json

from ...ml.benchmarking.historical_benchmark import HistoricalBenchmark
from ...ml.trajectories.generator import (
    TrajectoryGenerator,
)
from ..data.trajectory_dataset import (
    TrajectoryConverter,
    RLLMTrajectoryDataset,
)
from ..config.rllm_config import RLLMConfig


class BenchmarkIntegration:
    """Integration with benchmarking system."""

    def __init__(
        self,
        config: Optional[RLLMConfig] = None,
        output_dir: str = "./data/rllm",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize benchmark integration.

        Args:
            config: RLLM configuration
            output_dir: Output directory
            logger: Logger
        """
        self.config = config or RLLMConfig()
        self.output_dir = output_dir
        self.logger = logger or logging.getLogger("BenchmarkIntegration")

        os.makedirs(output_dir, exist_ok=True)

        self.historical_benchmark = HistoricalBenchmark()
        self.trajectory_generator = TrajectoryGenerator()
        self.trajectory_converter = TrajectoryConverter(output_dir=output_dir)

        self.logger.info("Initialized benchmark integration")

    async def run_benchmark_and_convert(
        self,
        issues: List[Dict[str, Any]],
        detailed_trajectories: bool = True,
        log_to_mlflow: bool = True,
        train_ratio: float = 0.8,
    ) -> Tuple[str, str, str]:
        """
        Run benchmark and convert trajectories to RLLM format.

        Args:
            issues: List of issues
            detailed_trajectories: Whether to generate detailed trajectories
            log_to_mlflow: Whether to log results to MLflow
            train_ratio: Ratio of training data

        Returns:
            Paths to benchmark result, training data, and validation data
        """
        self.logger.info(
            f"Running benchmark and converting {len(issues)} issues"
        )

        benchmark_result = await self.historical_benchmark.run_benchmark(
            issues=issues,
            detailed_trajectories=detailed_trajectories,
            log_to_mlflow=log_to_mlflow,
        )

        benchmark_id = benchmark_result.benchmark_id

        trajectories = await self.trajectory_generator.load_trajectories(
            f"trajectories_{benchmark_id}.json"
        )

        self.logger.info(
            f"Loaded {len(trajectories)} trajectories from benchmark {benchmark_id}"
        )

        train_path, val_path = (
            await self.trajectory_converter.create_train_val_split(
                trajectories=trajectories,
                train_ratio=train_ratio,
                train_filename=f"train_{benchmark_id}.jsonl",
                val_filename=f"val_{benchmark_id}.jsonl",
            )
        )

        self.logger.info(
            f"Converted trajectories to RLLM format: {train_path}, {val_path}"
        )

        result_path = os.path.join(
            self.output_dir, f"benchmark_{benchmark_id}.json"
        )
        with open(result_path, "w") as f:
            json.dump(benchmark_result.model_dump(), f, indent=2)

        self.logger.info(f"Saved benchmark result to {result_path}")

        return result_path, train_path, val_path

    async def load_training_data(
        self,
        train_path: str,
        val_path: Optional[str] = None,
        system_prompt: str = "You are a helpful AI assistant that solves software engineering issues.",
        max_length: int = 8192,
    ) -> Tuple[RLLMTrajectoryDataset, Optional[RLLMTrajectoryDataset]]:
        """
        Load training data from RLLM format.

        Args:
            train_path: Path to training data
            val_path: Path to validation data
            system_prompt: System prompt
            max_length: Maximum sequence length

        Returns:
            Training and validation datasets
        """
        self.logger.info(f"Loading training data from {train_path}")

        train_dataset = RLLMTrajectoryDataset.from_jsonl(
            path=train_path,
            system_prompt=system_prompt,
            max_length=max_length,
        )

        val_dataset = None
        if val_path:
            self.logger.info(f"Loading validation data from {val_path}")

            val_dataset = RLLMTrajectoryDataset.from_jsonl(
                path=val_path,
                system_prompt=system_prompt,
                max_length=max_length,
            )

        self.logger.info(
            f"Loaded {len(train_dataset)} training examples"
            + (
                f" and {len(val_dataset)} validation examples"
                if val_dataset
                else ""
            )
        )

        return train_dataset, val_dataset

    async def convert_existing_benchmark(
        self,
        benchmark_id: str,
        train_ratio: float = 0.8,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Convert existing benchmark to RLLM format.

        Args:
            benchmark_id: Benchmark ID
            train_ratio: Ratio of training data

        Returns:
            Paths to benchmark result, training data, and validation data
        """
        self.logger.info(
            f"Converting existing benchmark {benchmark_id} to RLLM format"
        )

        benchmark_result = (
            await self.historical_benchmark.load_benchmark_result(benchmark_id)
        )

        if not benchmark_result:
            self.logger.error(f"Benchmark result not found: {benchmark_id}")
            return None, None, None

        trajectories = await self.trajectory_generator.load_trajectories(
            f"trajectories_{benchmark_id}.json"
        )

        if not trajectories:
            self.logger.error(
                f"Trajectories not found for benchmark {benchmark_id}"
            )
            return None, None, None

        self.logger.info(
            f"Loaded {len(trajectories)} trajectories from benchmark {benchmark_id}"
        )

        train_path, val_path = (
            await self.trajectory_converter.create_train_val_split(
                trajectories=trajectories,
                train_ratio=train_ratio,
                train_filename=f"train_{benchmark_id}.jsonl",
                val_filename=f"val_{benchmark_id}.jsonl",
            )
        )

        self.logger.info(
            f"Converted trajectories to RLLM format: {train_path}, {val_path}"
        )

        result_path = os.path.join(
            self.output_dir, f"benchmark_{benchmark_id}.json"
        )
        with open(result_path, "w") as f:
            json.dump(benchmark_result.model_dump(), f, indent=2)

        self.logger.info(f"Saved benchmark result to {result_path}")

        return result_path, train_path, val_path
