"""
Integration with trajectory generation system.

This module provides integration between the RLLM framework and the
existing trajectory generation infrastructure.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..models.trajectory_models import BenchmarkTrajectory
from ..data.trajectory_dataset import TrajectoryConverter

from ..config.rllm_config import RLLMConfig


class TrajectoryIntegration:
    """Integration with trajectory generation system."""

    def __init__(
        self,
        config: Optional[RLLMConfig] = None,
        output_dir: str = "./data/rllm",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize trajectory integration.

        Args:
            config: RLLM configuration
            output_dir: Output directory
            logger: Logger
        """
        self.config = config or RLLMConfig()
        self.output_dir = output_dir
        self.logger = logger or logging.getLogger("TrajectoryIntegration")

        os.makedirs(output_dir, exist_ok=True)

        from ...ml.trajectories.generator import TrajectoryGenerator
        self.trajectory_generator = TrajectoryGenerator()
        self.trajectory_converter = TrajectoryConverter(output_dir=output_dir)

        self.logger.info("Initialized trajectory integration")

    async def generate_and_convert_trajectories(
        self,
        issues: List[Dict[str, Any]],
        detailed: bool = True,
        train_ratio: float = 0.8,
        output_prefix: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate and convert trajectories to RLLM format.

        Args:
            issues: List of issues
            detailed: Whether to generate detailed trajectories
            train_ratio: Ratio of training data
            output_prefix: Prefix for output files

        Returns:
            Paths to training and validation data
        """
        self.logger.info(
            f"Generating and converting trajectories for {len(issues)} issues"
        )

        trajectories = await self.trajectory_generator.generate_trajectories(
            issues=issues,
            detailed=detailed,
        )

        self.logger.info(f"Generated {len(trajectories)} trajectories")

        timestamp = int(datetime.now().timestamp())
        output_prefix = output_prefix or f"trajectories_{timestamp}"

        trajectories_path = await self.trajectory_generator.save_trajectories(
            trajectories=trajectories,
            filename=f"{output_prefix}.json",
        )

        self.logger.info(f"Saved trajectories to {trajectories_path}")

        train_path, val_path = (
            await self.trajectory_converter.create_train_val_split(
                trajectories=trajectories,
                train_ratio=train_ratio,
                train_filename=f"train_{output_prefix}.jsonl",
                val_filename=f"val_{output_prefix}.jsonl",
            )
        )

        self.logger.info(
            f"Converted trajectories to RLLM format: {train_path}, {val_path}"
        )

        return train_path, val_path

    async def convert_existing_trajectories(
        self,
        trajectories_path: str,
        train_ratio: float = 0.8,
        output_prefix: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert existing trajectories to RLLM format.

        Args:
            trajectories_path: Path to trajectories file
            train_ratio: Ratio of training data
            output_prefix: Prefix for output files

        Returns:
            Paths to training and validation data
        """
        self.logger.info(
            f"Converting existing trajectories from {trajectories_path}"
        )

        trajectories_dir, trajectories_filename = os.path.split(
            trajectories_path
        )

        current_dir = self.trajectory_generator.output_dir

        self.trajectory_generator.output_dir = trajectories_dir

        trajectories = await self.trajectory_generator.load_trajectories(
            trajectories_filename
        )

        self.trajectory_generator.output_dir = current_dir

        if not trajectories:
            self.logger.error(
                f"Failed to load trajectories from {trajectories_path}"
            )
            return None, None

        self.logger.info(f"Loaded {len(trajectories)} trajectories")

        timestamp = int(datetime.now().timestamp())
        output_prefix = output_prefix or f"trajectories_{timestamp}"

        train_path, val_path = (
            await self.trajectory_converter.create_train_val_split(
                trajectories=trajectories,
                train_ratio=train_ratio,
                train_filename=f"train_{output_prefix}.jsonl",
                val_filename=f"val_{output_prefix}.jsonl",
            )
        )

        self.logger.info(
            f"Converted trajectories to RLLM format: {train_path}, {val_path}"
        )

        return train_path, val_path

    async def filter_trajectories(
        self,
        trajectories: List[BenchmarkTrajectory],
        min_steps: int = 3,
        max_steps: Optional[int] = None,
        issue_types: Optional[List[str]] = None,
        repositories: Optional[List[str]] = None,
    ) -> List[BenchmarkTrajectory]:
        """
        Filter trajectories based on criteria.

        Args:
            trajectories: List of trajectories
            min_steps: Minimum number of steps
            max_steps: Maximum number of steps
            issue_types: List of issue types to include
            repositories: List of repositories to include

        Returns:
            Filtered trajectories
        """
        self.logger.info(f"Filtering {len(trajectories)} trajectories")

        filtered_trajectories = []

        for trajectory in trajectories:
            if len(trajectory.steps) < min_steps:
                continue

            if max_steps and len(trajectory.steps) > max_steps:
                continue

            if issue_types:
                issue_type = trajectory.metadata.get("issue_type")
                if not issue_type or issue_type not in issue_types:
                    continue

            if repositories:
                if trajectory.repository not in repositories:
                    continue

            filtered_trajectories.append(trajectory)

        self.logger.info(
            f"Filtered trajectories: {len(filtered_trajectories)} out of {len(trajectories)}"
        )

        return filtered_trajectories

    async def augment_trajectories(
        self,
        trajectories: List[BenchmarkTrajectory],
        augmentation_factor: int = 2,
    ) -> List[BenchmarkTrajectory]:
        """
        Augment trajectories by creating variations.

        Args:
            trajectories: List of trajectories
            augmentation_factor: Number of variations to create per trajectory

        Returns:
            Augmented trajectories
        """
        self.logger.info(f"Augmenting {len(trajectories)} trajectories")

        import random

        augmented_trajectories = []

        for trajectory in trajectories:
            augmented_trajectories.append(trajectory)

            for i in range(augmentation_factor - 1):
                augmented_trajectory = BenchmarkTrajectory(
                    issue_id=f"{trajectory.issue_id}_aug{i+1}",
                    issue_url=trajectory.issue_url,
                    repository=trajectory.repository,
                    metadata=trajectory.metadata.copy(),
                    source=trajectory.source,
                )

                if len(trajectory.steps) > 3:
                    steps = [trajectory.steps[0]]

                    middle_steps = trajectory.steps[1:-1]
                    num_middle_steps = random.randint(
                        max(1, len(middle_steps) // 2), len(middle_steps)
                    )

                    selected_middle_steps = random.sample(
                        middle_steps, num_middle_steps
                    )
                    steps.extend(selected_middle_steps)

                    steps.append(trajectory.steps[-1])

                    augmented_trajectory.steps = steps
                else:
                    augmented_trajectory.steps = trajectory.steps.copy()

                augmented_trajectories.append(augmented_trajectory)

        self.logger.info(
            f"Augmented trajectories: {len(augmented_trajectories)} from {len(trajectories)}"
        )

        return augmented_trajectories
