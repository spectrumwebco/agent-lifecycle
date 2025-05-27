"""
Convert trajectories to RLLM training format.

This module provides functionality to convert trajectories from
HistoricalBenchmark to RLLM training format.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field
from torch.utils.data import Dataset

from ..models.trajectory_models import BenchmarkTrajectory
from ..rust_bindings.utils import get_trajectory_dataset


class RLLMTrajectoryExample(BaseModel):
    """Single example for RLLM training."""

    input_text: str = Field(..., description="Input text")
    output_text: str = Field(..., description="Output text")
    reward: float = Field(0.0, description="Reward")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class RLLMTrajectoryDataset(Dataset):
    """Dataset for RLLM training from trajectories."""
    
    RustTrajectoryDataset = get_trajectory_dataset()

    def __init__(
        self,
        trajectories: List[BenchmarkTrajectory],
        system_prompt: str = "You are a helpful AI assistant that solves software engineering issues.",
        max_length: int = 8192,
    ):
        """
        Initialize dataset.

        Args:
            trajectories: List of trajectories
            system_prompt: System prompt
            max_length: Maximum sequence length
        """
        self.logger = logging.getLogger("RLLMTrajectoryDataset")
        self.system_prompt = system_prompt
        self.max_length = max_length
        
        if self.RustTrajectoryDataset is not None and hasattr(trajectories[0], "model_dump"):
            self.logger.info("Using Rust implementation for trajectory processing")
            # Convert trajectories to dict format for Rust
            trajectory_dicts = [traj.model_dump() for traj in trajectories]
            self._rust_dataset = self.RustTrajectoryDataset(trajectory_dicts, system_prompt, max_length)
            self.examples = self._convert_trajectories(trajectories)
        else:
            self.logger.info("Using Python implementation for trajectory processing")
            self._rust_dataset = None
            self.examples = self._convert_trajectories(trajectories)
            
        self.logger.info(f"Created dataset with {len(self.examples)} examples")

    def _convert_trajectories(
        self, trajectories: List[BenchmarkTrajectory]
    ) -> List[RLLMTrajectoryExample]:
        """
        Convert trajectories to RLLM examples.

        Args:
            trajectories: List of trajectories

        Returns:
            List of RLLM examples
        """
        examples = []

        for trajectory in trajectories:
            issue_id = trajectory.issue_id
            issue_url = trajectory.issue_url
            repository = trajectory.repository
            
            if len(trajectory.steps) < 2:
                self.logger.warning(f"Skipping trajectory {issue_id} with insufficient steps")
                continue
                
            issue_step = trajectory.steps[0]
            analysis_step = trajectory.steps[1]
            
            input_text = f"{self.system_prompt}\n\n"
            input_text += f"Repository: {repository}\n"
            input_text += f"Issue: {issue_step.observation}\n\n"
            input_text += "Analyze this issue and provide a solution."
            
            output_text = analysis_step.response
            
            reward = 1.0  # Base reward for completed trajectory
            
            example = RLLMTrajectoryExample(
                input_text=input_text,
                output_text=output_text,
                reward=reward,
                metadata={
                    "issue_id": issue_id,
                    "issue_url": issue_url,
                    "repository": repository,
                    "steps_count": len(trajectory.steps),
                    "source": trajectory.source,
                },
            )
            
            examples.append(example)
            
            if len(trajectory.steps) > 3:
                for i in range(2, len(trajectory.steps) - 1):
                    current_step = trajectory.steps[i]
                    next_step = trajectory.steps[i + 1]
                    
                    context = "\n\n".join([
                        f"Step {j+1}: {step.action}\n{step.observation}\n{step.response}"
                        for j, step in enumerate(trajectory.steps[:i])
                    ])
                    
                    input_text = f"{self.system_prompt}\n\n"
                    input_text += f"Repository: {repository}\n"
                    input_text += f"Issue: {issue_step.observation}\n\n"
                    input_text += f"Previous steps:\n{context}\n\n"
                    input_text += f"Current step: {current_step.action}\n{current_step.observation}\n"
                    input_text += "Provide the next response."
                    
                    output_text = next_step.response
                    
                    step_reward = 1.0 * (i + 1) / len(trajectory.steps)
                    
                    example = RLLMTrajectoryExample(
                        input_text=input_text,
                        output_text=output_text,
                        reward=step_reward,
                        metadata={
                            "issue_id": issue_id,
                            "issue_url": issue_url,
                            "repository": repository,
                            "step_index": i,
                            "steps_count": len(trajectory.steps),
                            "source": trajectory.source,
                        },
                    )
                    
                    examples.append(example)
        
        return examples

    def __len__(self) -> int:
        """Get dataset length."""
        return len(self.examples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        Get item by index.

        Args:
            idx: Index

        Returns:
            Item
        """
        example = self.examples[idx]
        
        return {
            "input_text": example.input_text,
            "output_text": example.output_text,
            "reward": example.reward,
            "metadata": example.metadata,
        }

    def save_to_jsonl(self, path: str) -> None:
        """
        Save dataset to JSONL file.

        Args:
            path: Output path
        """
        if self._rust_dataset is not None:
            self.logger.info("Using Rust implementation for saving to JSONL")
            self._rust_dataset.save_to_jsonl(path)
        else:
            with open(path, "w") as f:
                for example in self.examples:
                    f.write(json.dumps(example.model_dump()) + "\n")
        
        self.logger.info(f"Saved {len(self.examples)} examples to {path}")

    @classmethod
    def from_jsonl(cls, path: str, system_prompt: Optional[str] = "", max_length: Optional[int] = 0) -> "RLLMTrajectoryDataset":
        """
        Load dataset from JSONL file.

        Args:
            path: Input path
            system_prompt: System prompt
            max_length: Maximum sequence length

        Returns:
            Dataset
        """
        logger = logging.getLogger("RLLMTrajectoryDataset")
        
        if not os.path.exists(path):
            logger.error(f"Dataset file not found: {path}")
            dataset = cls.__new__(cls)
            dataset.logger = logger
            dataset.system_prompt = "You are a helpful AI assistant that solves software engineering issues."
            dataset.max_length = 8192
            dataset.examples = []
            dataset._rust_dataset = None
            return dataset
        
        RustTrajectoryDataset = get_trajectory_dataset()
        
        if RustTrajectoryDataset is not None:
            logger.info("Using Rust implementation for loading from JSONL")
            system_prompt = system_prompt or "You are a helpful AI assistant that solves software engineering issues."
            max_length = max_length or 8192
            
            dataset = cls.__new__(cls)
            dataset.logger = logger
            dataset.system_prompt = system_prompt
            dataset.max_length = max_length
            
            dataset._rust_dataset = RustTrajectoryDataset.from_jsonl(path, system_prompt, max_length)
            
            examples = []
            with open(path, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    example = RLLMTrajectoryExample(**data)
                    examples.append(example)
            
            dataset.examples = examples
            logger.info(f"Loaded {len(examples)} examples from {path}")
            
            return dataset
        else:
            logger.info("Using Python implementation for loading from JSONL")
            examples = []
            
            with open(path, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    example = RLLMTrajectoryExample(**data)
                    examples.append(example)
            
            logger.info(f"Loaded {len(examples)} examples from {path}")
            
            dataset = cls.__new__(cls)
            dataset.logger = logger
            dataset.system_prompt = system_prompt or "You are a helpful AI assistant that solves software engineering issues."
            dataset.max_length = max_length or 8192
            dataset.examples = examples
            dataset._rust_dataset = None
            
            return dataset


class TrajectoryConverter:
    """Converter for trajectories to RLLM format."""

    def __init__(
        self,
        output_dir: str = "./data/rllm",
        system_prompt: str = "You are a helpful AI assistant that solves software engineering issues.",
        max_length: int = 8192,
    ):
        """
        Initialize converter.

        Args:
            output_dir: Output directory
            system_prompt: System prompt
            max_length: Maximum sequence length
        """
        self.output_dir = output_dir
        self.system_prompt = system_prompt
        self.max_length = max_length
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.logger = logging.getLogger("TrajectoryConverter")

    async def convert_trajectories(
        self,
        trajectories: List[BenchmarkTrajectory],
        output_filename: str = "trajectories.jsonl",
    ) -> str:
        """
        Convert trajectories to RLLM format.

        Args:
            trajectories: List of trajectories
            output_filename: Output filename

        Returns:
            Path to output file
        """
        self.logger.info(f"Converting {len(trajectories)} trajectories to RLLM format")
        
        dataset = RLLMTrajectoryDataset(
            trajectories=trajectories,
            system_prompt=self.system_prompt,
            max_length=self.max_length,
        )
        
        output_path = os.path.join(self.output_dir, output_filename)
        dataset.save_to_jsonl(output_path)
        
        self.logger.info(f"Saved RLLM dataset to {output_path}")
        
        return output_path

    async def create_train_val_split(
        self,
        trajectories: List[BenchmarkTrajectory],
        train_ratio: float = 0.8,
        train_filename: str = "train.jsonl",
        val_filename: str = "val.jsonl",
    ) -> Tuple[str, str]:
        """
        Create train/validation split.

        Args:
            trajectories: List of trajectories
            train_ratio: Ratio of training data
            train_filename: Training filename
            val_filename: Validation filename

        Returns:
            Paths to training and validation files
        """
        self.logger.info(f"Creating train/val split for {len(trajectories)} trajectories")
        
        import random
        random.shuffle(trajectories)
        
        split_idx = int(len(trajectories) * train_ratio)
        train_trajectories = trajectories[:split_idx]
        val_trajectories = trajectories[split_idx:]
        
        self.logger.info(f"Split: {len(train_trajectories)} train, {len(val_trajectories)} validation")
        
        train_path = await self.convert_trajectories(train_trajectories, train_filename)
        val_path = await self.convert_trajectories(val_trajectories, val_filename)
        
        return train_path, val_path
