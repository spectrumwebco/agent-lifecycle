"""
RLLM model trainer.

This module provides functionality for training RLLM models
on trajectory data from historical benchmarks.
"""

import os
import json
import logging
from typing import Dict, Optional, Tuple
import torch

from ..config.rllm_config import RLLMConfig, RLLMTrainingConfig
from ..models.rllm_model import RLLMModel
from ..rewards.issue_rewards import RewardCalculator
from ..data.trajectory_dataset import (
    RLLMTrajectoryDataset,
)
from .distributed import DistributedTrainer


class RLLMTrainer:
    """Trainer for RLLM models."""

    def __init__(
        self,
        config: Optional[RLLMConfig] = None,
        training_config: Optional[RLLMTrainingConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize trainer.

        Args:
            config: RLLM configuration
            training_config: Training configuration
            logger: Logger
        """
        self.config = config or RLLMConfig()
        self.training_config = training_config or self.config.training
        self.logger = logger or logging.getLogger("RLLMTrainer")

        self.model = None
        self.reward_calculator = RewardCalculator(
            config=self.config.reward, logger=self.logger
        )

        self.logger.info(
            f"Initialized RLLM trainer with config: {self.training_config.model_dump()}"
        )

    def load_model(
        self, model_id: Optional[str] = None, device: Optional[str] = None
    ) -> None:
        """
        Load model.

        Args:
            model_id: Model ID
            device: Device to use
        """
        model_id = model_id or self.config.model.model_id

        self.logger.info(f"Loading model: {model_id}")

        self.model = RLLMModel(
            model_config=self.config.model,
            device=device,
            logger=self.logger,
        )

        self.model.load_model()

        self.logger.info("Model loaded successfully")

    def prepare_data(
        self,
        trajectories_path: str,
        output_dir: Optional[str] = None,
        train_ratio: float = 0.8,
    ) -> Tuple[str, str]:
        """
        Prepare data for training.

        Args:
            trajectories_path: Path to trajectories
            output_dir: Output directory
            train_ratio: Ratio of training data

        Returns:
            Paths to training and validation data
        """
        self.logger.info(f"Preparing data from {trajectories_path}")

        output_dir = output_dir or os.path.join(
            self.config.model.output_dir, "data"
        )
        os.makedirs(output_dir, exist_ok=True)

        trajectories = []

        try:
            with open(trajectories_path, "r") as f:
                for line in f:
                    trajectory = json.loads(line.strip())
                    trajectories.append(trajectory)

            self.logger.info(
                f"Loaded {len(trajectories)} trajectories from {trajectories_path}"
            )

        except Exception as e:
            self.logger.error(f"Error loading trajectories: {e}")
            raise

        # converter = TrajectoryConverter(
        #     output_dir=output_dir,
        #     system_prompt=self.training_config.system_prompt,
        #     max_length=self.training_config.max_length,
        # )

        import random

        random.shuffle(trajectories)

        split_idx = int(len(trajectories) * train_ratio)
        train_trajectories = trajectories[:split_idx]
        val_trajectories = trajectories[split_idx:]

        self.logger.info(
            f"Split: {len(train_trajectories)} train, {len(val_trajectories)} validation"
        )

        train_path = os.path.join(output_dir, "train.jsonl")
        val_path = os.path.join(output_dir, "val.jsonl")

        train_dataset = RLLMTrajectoryDataset(
            trajectories=train_trajectories,
            system_prompt=self.training_config.system_prompt,
            max_length=self.training_config.max_length,
        )

        val_dataset = RLLMTrajectoryDataset(
            trajectories=val_trajectories,
            system_prompt=self.training_config.system_prompt,
            max_length=self.training_config.max_length,
        )

        train_dataset.save_to_jsonl(train_path)
        val_dataset.save_to_jsonl(val_path)

        self.logger.info(f"Saved training data to {train_path}")
        self.logger.info(f"Saved validation data to {val_path}")

        return train_path, val_path

    def train(
        self,
        train_data_path: str,
        val_data_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        num_epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        learning_rate: Optional[float] = None,
        distributed: bool = False,
        num_workers: Optional[int] = None,
    ) -> Optional[str]:
        """
        Train model.

        Args:
            train_data_path: Path to training data
            val_data_path: Path to validation data
            output_dir: Output directory
            num_epochs: Number of epochs
            batch_size: Batch size
            learning_rate: Learning rate
            distributed: Whether to use distributed training
            num_workers: Number of workers for distributed training

        Returns:
            Path to trained model
        """
        self.logger.info(f"Starting training with data: {train_data_path}")

        num_epochs = num_epochs or self.training_config.num_epochs
        batch_size = batch_size or self.training_config.batch_size
        learning_rate = learning_rate or self.training_config.learning_rate
        output_dir = output_dir or self.config.model.output_dir

        os.makedirs(output_dir, exist_ok=True)

        if distributed:
            self.logger.info("Using distributed training")

            trainer = DistributedTrainer(
                config=self.config,
                logger=self.logger,
            )

            return trainer.train(
                train_data_path=train_data_path,
                val_data_path=val_data_path,
                output_dir=output_dir,
                num_epochs=num_epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                num_workers=num_workers,
            )

        if self.model is None:
            self.load_model()

        if self.model is None:
            self.logger.error("Failed to load model for training")
            return None

        self.model.prepare_for_training()

        self.logger.info(f"Loading training data from {train_data_path}")

        train_dataset = RLLMTrajectoryDataset.from_jsonl(
            path=train_data_path,
            system_prompt=self.training_config.system_prompt,
            max_length=self.training_config.max_length,
        )

        val_dataset = None
        if val_data_path:
            self.logger.info(f"Loading validation data from {val_data_path}")

            val_dataset = RLLMTrajectoryDataset.from_jsonl(
                path=val_data_path,
                system_prompt=self.training_config.system_prompt,
                max_length=self.training_config.max_length,
            )

        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0,  # Use 0 for single-process training
        )

        val_loader = None
        if val_dataset:
            val_loader = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=0,  # Use 0 for single-process training
            )

        if self.model is None or not hasattr(self.model, "model"):
            self.logger.error("Model not properly initialized for training")
            return None

        optimizer = torch.optim.AdamW(
            self.model.model.parameters(),
            lr=learning_rate,
            weight_decay=self.training_config.weight_decay,
        )

        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=num_epochs * len(train_loader),
        )

        self.logger.info("Starting training loop")

        for epoch in range(num_epochs):
            self.logger.info(f"Starting epoch {epoch + 1}/{num_epochs}")

            if self.model is None or not hasattr(self.model, "model"):
                self.logger.error(
                    "Model not properly initialized for training loop"
                )
                return None

            self.model.model.train()

            total_loss = 0.0

            for batch_idx, batch in enumerate(train_loader):
                input_texts = batch["input_text"]
                output_texts = batch["output_text"]
                rewards = torch.tensor([batch["reward"]], dtype=torch.float32)

                inputs = self.model.tokenizer(
                    input_texts,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                    max_length=self.training_config.max_length,
                ).to(self.model.device)

                outputs = self.model.tokenizer(
                    output_texts,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                    max_length=self.training_config.max_length,
                ).to(self.model.device)

                model_outputs = self.model.model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    labels=outputs["input_ids"],
                )

                loss = model_outputs.loss

                if self.training_config.use_rewards:
                    scaled_rewards = 0.1 + 1.9 * (rewards - rewards.min()) / (
                        rewards.max() - rewards.min() + 1e-8
                    )
                    scaled_rewards = scaled_rewards.to(self.model.device)

                    loss = loss * scaled_rewards.mean()

                loss.backward()

                if self.training_config.max_grad_norm > 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.model.parameters(),
                        self.training_config.max_grad_norm,
                    )

                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

                total_loss += loss.item()

                if (batch_idx + 1) % 10 == 0 or batch_idx == len(
                    train_loader
                ) - 1:
                    self.logger.info(
                        f"Epoch {epoch + 1}/{num_epochs}, "
                        f"Batch {batch_idx + 1}/{len(train_loader)}, "
                        f"Loss: {loss.item():.4f}, "
                        f"LR: {scheduler.get_last_lr()[0]:.8f}"
                    )

            avg_loss = total_loss / len(train_loader)
            self.logger.info(
                f"Epoch {epoch + 1}/{num_epochs} completed, Average Loss: {avg_loss:.4f}"
            )

            if val_loader:
                self.logger.info("Evaluating on validation data")

                self.model.model.eval()
                val_loss = 0.0

                with torch.no_grad():
                    for batch_idx, batch in enumerate(val_loader):
                        input_texts = batch["input_text"]
                        output_texts = batch["output_text"]

                        inputs = self.model.tokenizer(
                            input_texts,
                            padding=True,
                            truncation=True,
                            return_tensors="pt",
                            max_length=self.training_config.max_length,
                        ).to(self.model.device)

                        outputs = self.model.tokenizer(
                            output_texts,
                            padding=True,
                            truncation=True,
                            return_tensors="pt",
                            max_length=self.training_config.max_length,
                        ).to(self.model.device)

                        model_outputs = self.model.model(
                            input_ids=inputs["input_ids"],
                            attention_mask=inputs["attention_mask"],
                            labels=outputs["input_ids"],
                        )

                        batch_loss = model_outputs.loss.item()
                        val_loss += batch_loss

                avg_val_loss = val_loss / len(val_loader)
                self.logger.info(f"Validation Loss: {avg_val_loss:.4f}")

        self.logger.info(f"Saving model to {output_dir}")

        self.model.save_model(output_dir)

        self.logger.info("Training completed successfully")

        return output_dir

    def evaluate(
        self,
        test_data_path: str,
        model_path: Optional[str] = None,
        batch_size: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        Evaluate model.

        Args:
            test_data_path: Path to test data
            model_path: Path to model
            batch_size: Batch size

        Returns:
            Evaluation metrics
        """
        self.logger.info(f"Evaluating model on {test_data_path}")

        if model_path:
            self.model = RLLMModel.from_pretrained(model_path)

        if self.model is None:
            self.load_model()

        self.model.prepare_for_inference()

        test_dataset = RLLMTrajectoryDataset.from_jsonl(
            path=test_data_path,
            system_prompt=self.training_config.system_prompt,
            max_length=self.training_config.max_length,
        )

        batch_size = batch_size or self.training_config.batch_size

        test_loader = torch.utils.data.DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,  # Use 0 for single-process evaluation
        )

        self.model.model.eval()

        total_loss = 0.0
        total_samples = 0

        with torch.no_grad():
            for batch_idx, batch in enumerate(test_loader):
                input_texts = batch["input_text"]
                output_texts = batch["output_text"]

                inputs = self.model.tokenizer(
                    input_texts,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                    max_length=self.training_config.max_length,
                ).to(self.model.device)

                outputs = self.model.tokenizer(
                    output_texts,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                    max_length=self.training_config.max_length,
                ).to(self.model.device)

                model_outputs = self.model.model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    labels=outputs["input_ids"],
                )

                batch_loss = model_outputs.loss.item()
                total_loss += batch_loss * len(input_texts)
                total_samples += len(input_texts)

                if (batch_idx + 1) % 10 == 0 or batch_idx == len(
                    test_loader
                ) - 1:
                    self.logger.info(
                        f"Batch {batch_idx + 1}/{len(test_loader)}, "
                        f"Loss: {batch_loss:.4f}"
                    )

        avg_loss = total_loss / total_samples

        metrics = {
            "loss": avg_loss,
        }

        self.logger.info(f"Evaluation completed, metrics: {metrics}")

        return metrics

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        do_sample: bool = True,
    ) -> Optional[str]:
        """
        Generate text.

        Args:
            prompt: Prompt
            max_new_tokens: Maximum number of new tokens
            temperature: Temperature
            top_p: Top p
            top_k: Top k
            repetition_penalty: Repetition penalty
            do_sample: Whether to sample

        Returns:
            Generated text
        """
        if self.model is None:
            self.load_model()

        self.model.prepare_for_inference()

        return self.model.generate(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            do_sample=do_sample,
        )
