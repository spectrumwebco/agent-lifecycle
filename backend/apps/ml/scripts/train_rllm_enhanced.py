"""
Enhanced training script for RLLM models on historical issue trajectories.

This script provides a comprehensive interface for training RLLM models
on historical issue trajectories with support for:
- Training from historical benchmarks or existing trajectory data
- Distributed training with Ray
- MLflow experiment tracking
- Model checkpointing and early stopping
- Hyperparameter tuning with Optuna
- Detailed progress tracking and visualization
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

import numpy as np
import optuna
from tqdm.asyncio import tqdm

from ..config.rllm_config import (
    RLLMConfig,
    RLLMModelConfig,
    RLLMTrainingConfig,
    RLLMDistributedConfig,
    RLLMRewardConfig,
    get_deepcoder_config,
)
from ..training.trainer import RLLMTrainer
from ..training.distributed import DistributedTrainer
from ..integration.benchmark_integration import BenchmarkIntegration
from ..integration.trajectory_integration import TrajectoryIntegration
from ..integration.ml_integration import MLIntegration
from ..rewards.issue_rewards import RewardCalculator


class TrainingManager:
    """Manager for RLLM training workflows."""

    def __init__(
        self,
        config: Optional[RLLMConfig] = None,
        output_dir: str = "./data/rllm",
        experiment_name: str = "rllm_training",
        run_name: Optional[str] = None,
        log_to_mlflow: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize training manager."""
        self.config = config or get_deepcoder_config()
        self.output_dir = output_dir
        self.experiment_name = experiment_name
        self.run_name = run_name or f"rllm_{int(datetime.now().timestamp())}"
        self.log_to_mlflow = log_to_mlflow
        self.logger = logger or logging.getLogger("TrainingManager")

        os.makedirs(output_dir, exist_ok=True)

        self.benchmark_integration = BenchmarkIntegration(
            config=self.config,
            output_dir=self.output_dir,
            logger=self.logger,
        )

        self.trajectory_integration = TrajectoryIntegration(
            config=self.config,
            output_dir=self.output_dir,
            logger=self.logger,
        )

        self.ml_integration = MLIntegration(
            config=self.config,
            logger=self.logger,
        )

        if self.config.distributed and self.config.distributed.enabled:
            self.trainer = DistributedTrainer(
                config=self.config,
                logger=self.logger,
            )
        else:
            self.trainer = RLLMTrainer(
                config=self.config,
                logger=self.logger,
            )

        self.mlflow_run_id = None
        self.best_model_path = None
        self.best_val_loss = float("inf")
        self.best_val_reward = float("-inf")
        self.early_stop_counter = 0
        self.early_stop_patience = self.config.training.early_stop_patience if hasattr(self.config.training, "early_stop_patience") else 3

    async def setup_mlflow(self) -> None:
        """Set up MLflow for experiment tracking."""
        if not self.log_to_mlflow:
            return

        try:
            await self.ml_integration.setup_mlflow(
                experiment_name=self.experiment_name
            )
            self.logger.info(f"MLflow set up with experiment: {self.experiment_name}")
        except Exception as e:
            self.logger.error(f"Failed to set up MLflow: {e}")
            self.log_to_mlflow = False

    async def prepare_data(
        self,
        benchmark_id: Optional[str] = None,
        train_path: Optional[str] = None,
        val_path: Optional[str] = None,
        test_size: float = 0.2,
        random_seed: int = 42,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Prepare training data."""
        if train_path is None and benchmark_id is not None:
            self.logger.info(f"Converting benchmark {benchmark_id} to RLLM format")
            try:
                result_path, train_path, val_path = (
                    await self.benchmark_integration.convert_existing_benchmark(
                        benchmark_id=benchmark_id,
                        test_size=test_size,
                        random_seed=random_seed,
                    )
                )

                if train_path is None:
                    self.logger.error(f"Failed to convert benchmark {benchmark_id}")
                    return None, None

                self.logger.info(f"Benchmark converted successfully: {result_path}")
            except Exception as e:
                self.logger.error(f"Error converting benchmark: {e}")
                return None, None

        if train_path is None:
            self.logger.error("No training data provided")
            return None, None

        if not os.path.exists(train_path):
            self.logger.error(f"Training data not found: {train_path}")
            return None, None

        if val_path and not os.path.exists(val_path):
            self.logger.warning(f"Validation data not found: {val_path}")
            val_path = None

        self.logger.info(f"Using training data: {train_path}")
        if val_path:
            self.logger.info(f"Using validation data: {val_path}")
        else:
            self.logger.warning("No validation data provided")

        return train_path, val_path

    async def log_training_start(self) -> Optional[str]:
        """Log training start to MLflow."""
        if not self.log_to_mlflow:
            return None

        try:
            config_dict = self.config.model_dump()
            
            metadata = {
                "start_time": datetime.now().isoformat(),
                "output_dir": self.output_dir,
                "run_name": self.run_name,
            }
            
            config_dict["metadata"] = metadata

            self.mlflow_run_id = await self.ml_integration.log_training_start(
                run_id=self.run_name,
                config=config_dict,
            )
            
            self.logger.info(f"Training start logged to MLflow with run ID: {self.mlflow_run_id}")
            return self.mlflow_run_id
        except Exception as e:
            self.logger.error(f"Failed to log training start: {e}")
            return None

    async def log_metrics(
        self, 
        metrics: Dict[str, float], 
        step: Optional[int] = None
    ) -> None:
        """Log metrics to MLflow."""
        if not self.log_to_mlflow or not self.mlflow_run_id:
            return

        try:
            await self.ml_integration.log_metrics(
                run_id=self.mlflow_run_id,
                metrics=metrics,
                step=step,
            )
            
            self.logger.debug(f"Metrics logged to MLflow: {metrics}")
        except Exception as e:
            self.logger.error(f"Failed to log metrics: {e}")

    async def log_training_end(
        self, 
        metrics: Dict[str, float], 
        artifacts: Optional[List[str]] = None
    ) -> None:
        """Log training end to MLflow."""
        if not self.log_to_mlflow or not self.mlflow_run_id:
            return

        try:
            artifacts = artifacts or []
            if self.best_model_path and os.path.exists(self.best_model_path):
                artifacts.append(self.best_model_path)

            await self.ml_integration.log_training_end(
                run_id=self.mlflow_run_id,
                metrics=metrics,
                artifacts=artifacts,
            )
            
            self.logger.info(f"Training end logged to MLflow with metrics: {metrics}")
        except Exception as e:
            self.logger.error(f"Failed to log training end: {e}")

    async def check_early_stopping(
        self, 
        val_metrics: Dict[str, float], 
        epoch: int
    ) -> bool:
        """Check if early stopping criteria are met."""
        if not hasattr(self.config.training, "early_stopping") or not self.config.training.early_stopping:
            return False

        improved = False
        
        if "loss" in val_metrics and val_metrics["loss"] < self.best_val_loss:
            self.best_val_loss = val_metrics["loss"]
            improved = True
            
        if "reward" in val_metrics and val_metrics["reward"] > self.best_val_reward:
            self.best_val_reward = val_metrics["reward"]
            improved = True

        if improved:
            self.early_stop_counter = 0
            return False
        else:
            self.early_stop_counter += 1
            
            if self.early_stop_counter >= self.early_stop_patience:
                self.logger.info(f"Early stopping triggered after {epoch + 1} epochs")
                return True
                
            return False

    async def save_checkpoint(
        self, 
        model_path: str, 
        val_metrics: Dict[str, float], 
        epoch: int
    ) -> None:
        """Save model checkpoint."""
        is_best = False
        
        if "loss" in val_metrics and val_metrics["loss"] < self.best_val_loss:
            self.best_val_loss = val_metrics["loss"]
            is_best = True
            
        if "reward" in val_metrics and val_metrics["reward"] > self.best_val_reward:
            self.best_val_reward = val_metrics["reward"]
            is_best = True

        checkpoint_dir = os.path.join(self.output_dir, "checkpoints")
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        checkpoint_path = os.path.join(checkpoint_dir, f"checkpoint_epoch_{epoch + 1}")
        os.makedirs(checkpoint_path, exist_ok=True)
        
        import shutil
        for item in os.listdir(model_path):
            src = os.path.join(model_path, item)
            dst = os.path.join(checkpoint_path, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
                
        with open(os.path.join(checkpoint_path, "metrics.json"), "w") as f:
            json.dump(val_metrics, f, indent=2)
            
        self.logger.info(f"Checkpoint saved at epoch {epoch + 1}: {checkpoint_path}")
        
        if is_best:
            self.best_model_path = checkpoint_path
            self.logger.info(f"New best model at epoch {epoch + 1}")
            
            best_model_link = os.path.join(self.output_dir, "best_model")
            if os.path.exists(best_model_link) and os.path.islink(best_model_link):
                os.unlink(best_model_link)
                
            os.symlink(checkpoint_path, best_model_link, target_is_directory=True)

    async def train(
        self,
        train_path: str,
        val_path: Optional[str] = None,
        num_epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        learning_rate: Optional[float] = None,
        distributed: Optional[bool] = None,
        checkpoint_interval: int = 1,
    ) -> Optional[str]:
        """Train RLLM model."""
        if num_epochs is not None:
            self.config.training.num_epochs = num_epochs
            
        if batch_size is not None:
            self.config.training.batch_size = batch_size
            
        if learning_rate is not None:
            self.config.training.learning_rate = learning_rate
            
        if distributed is not None:
            if not hasattr(self.config, "distributed"):
                self.config.distributed = RLLMDistributedConfig(enabled=distributed)
            else:
                self.config.distributed.enabled = distributed

        await self.log_training_start()

        try:
            model_path = await self.trainer.train(
                train_data_path=train_path,
                val_data_path=val_path,
                distributed=self.config.distributed.enabled if hasattr(self.config, "distributed") else False,
                num_epochs=self.config.training.num_epochs,
                batch_size=self.config.training.batch_size,
                learning_rate=self.config.training.learning_rate,
                checkpoint_callback=self.save_checkpoint,
                early_stopping_callback=self.check_early_stopping,
                metrics_callback=self.log_metrics,
                checkpoint_interval=checkpoint_interval,
            )

            if model_path:
                self.logger.info(f"Model trained successfully: {model_path}")
                
                final_metrics = {
                    "training_completed": 1.0,
                    "best_val_loss": self.best_val_loss if self.best_val_loss != float("inf") else 0.0,
                    "best_val_reward": self.best_val_reward if self.best_val_reward != float("-inf") else 0.0,
                }
                
                await self.log_training_end(
                    metrics=final_metrics,
                    artifacts=[model_path],
                )
                
                return model_path
            else:
                self.logger.error("Training failed")
                
                await self.log_training_end(
                    metrics={"training_completed": 0.0},
                )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error during training: {e}")
            
            await self.log_training_end(
                metrics={"training_completed": 0.0, "error": 1.0},
            )
            
            return None

    async def tune_hyperparameters(
        self,
        train_path: str,
        val_path: Optional[str] = None,
        n_trials: int = 10,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Tune hyperparameters using Optuna."""
        self.logger.info(f"Starting hyperparameter tuning with {n_trials} trials")
        
        async def objective(trial):
            learning_rate = trial.suggest_float("learning_rate", 1e-6, 1e-4, log=True)
            batch_size = trial.suggest_categorical("batch_size", [2, 4, 8, 16])
            num_epochs = trial.suggest_int("num_epochs", 1, 5)
            
            trial_config = self.config.copy(deep=True)
            trial_config.training.learning_rate = learning_rate
            trial_config.training.batch_size = batch_size
            trial_config.training.num_epochs = num_epochs
            
            trial_trainer = RLLMTrainer(
                config=trial_config,
                output_dir=os.path.join(self.output_dir, f"trial_{trial.number}"),
                logger=self.logger,
            )
            
            try:
                model_path, metrics = await trial_trainer.train_with_metrics(
                    train_data_path=train_path,
                    val_data_path=val_path,
                )
                
                if model_path and "val_loss" in metrics:
                    val_loss = metrics["val_loss"]
                    
                    if self.log_to_mlflow and self.mlflow_run_id:
                        trial_metrics = {
                            f"trial_{trial.number}_learning_rate": learning_rate,
                            f"trial_{trial.number}_batch_size": batch_size,
                            f"trial_{trial.number}_num_epochs": num_epochs,
                            f"trial_{trial.number}_val_loss": val_loss,
                        }
                        
                        await self.log_metrics(trial_metrics)
                    
                    return val_loss
                else:
                    return float("inf")
                    
            except Exception as e:
                self.logger.error(f"Error in trial {trial.number}: {e}")
                return float("inf")
        
        study = optuna.create_study(direction="minimize")
        
        await optuna.integration.aiohttp.AioHttpStorage.optimize(
            study,
            objective,
            n_trials=n_trials,
            timeout=timeout,
        )
        
        best_params = study.best_params
        best_value = study.best_value
        
        self.logger.info(f"Best hyperparameters: {best_params}, best value: {best_value}")
        
        self.config.training.learning_rate = best_params["learning_rate"]
        self.config.training.batch_size = best_params["batch_size"]
        self.config.training.num_epochs = best_params["num_epochs"]
        
        if self.log_to_mlflow and self.mlflow_run_id:
            best_metrics = {
                "best_learning_rate": best_params["learning_rate"],
                "best_batch_size": best_params["batch_size"],
                "best_num_epochs": best_params["num_epochs"],
                "best_val_loss": best_value,
            }
            
            await self.log_metrics(best_metrics)
        
        return best_params


async def train_on_historical_issues(
    config_path: Optional[str] = None,
    benchmark_id: Optional[str] = None,
    train_path: Optional[str] = None,
    val_path: Optional[str] = None,
    output_dir: str = "./data/rllm",
    distributed: bool = False,
    log_to_mlflow: bool = True,
    num_epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 5e-5,
    checkpoint_interval: int = 1,
    early_stopping: bool = True,
    early_stop_patience: int = 3,
    tune_hyperparameters: bool = False,
    n_trials: int = 10,
    experiment_name: str = "rllm_training",
    run_name: Optional[str] = None,
    verbose: bool = False,
):
    """Train RLLM model on historical issues."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger("train_rllm_enhanced")
    logger.setLevel(log_level)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    os.makedirs(output_dir, exist_ok=True)
    file_handler = logging.FileHandler(
        os.path.join(output_dir, "training.log")
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)

    if config_path and os.path.exists(config_path):
        config = RLLMConfig.from_json(config_path)
        logger.info(f"Loaded configuration from {config_path}")
    else:
        config = get_deepcoder_config()
        logger.info("Using default DeepCoder configuration")

    config.training.num_epochs = num_epochs
    config.training.batch_size = batch_size
    config.training.learning_rate = learning_rate
    config.training.early_stopping = early_stopping
    config.training.early_stop_patience = early_stop_patience
    
    if not hasattr(config, "distributed"):
        config.distributed = RLLMDistributedConfig(enabled=distributed)
    else:
        config.distributed.enabled = distributed

    training_manager = TrainingManager(
        config=config,
        output_dir=output_dir,
        experiment_name=experiment_name,
        run_name=run_name,
        log_to_mlflow=log_to_mlflow,
        logger=logger,
    )

    await training_manager.setup_mlflow()

    train_data_path, val_data_path = await training_manager.prepare_data(
        benchmark_id=benchmark_id,
        train_path=train_path,
        val_path=val_path,
    )

    if train_data_path is None:
        logger.error("Failed to prepare training data")
        return

    if tune_hyperparameters:
        logger.info("Tuning hyperparameters")
        best_params = await training_manager.tune_hyperparameters(
            train_path=train_data_path,
            val_path=val_data_path,
            n_trials=n_trials,
        )
        
        logger.info(f"Best hyperparameters: {best_params}")
        
        config.training.learning_rate = best_params["learning_rate"]
        config.training.batch_size = best_params["batch_size"]
        config.training.num_epochs = best_params["num_epochs"]

    logger.info("Starting training")
    model_path = await training_manager.train(
        train_path=train_data_path,
        val_path=val_data_path,
        checkpoint_interval=checkpoint_interval,
    )

    if model_path:
        logger.info(f"Model saved to {model_path}")
        
        best_model_path = os.path.join(output_dir, "best_model")
        if os.path.exists(best_model_path) and os.path.islink(best_model_path):
            real_path = os.path.realpath(best_model_path)
            logger.info(f"Best model available at {real_path}")
            return real_path
        
        return model_path
    else:
        logger.error("Training failed")
        return None


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(
        description="Enhanced training script for RLLM models on historical issues"
    )
    
    data_group = parser.add_argument_group("Data Parameters")
    data_group.add_argument(
        "--config", type=str, help="Path to configuration file"
    )
    data_group.add_argument(
        "--benchmark-id", type=str, help="Benchmark ID to use for training"
    )
    data_group.add_argument(
        "--train-path", type=str, help="Path to training data"
    )
    data_group.add_argument(
        "--val-path", type=str, help="Path to validation data"
    )
    data_group.add_argument(
        "--output-dir",
        type=str,
        default="./data/rllm",
        help="Output directory",
    )
    
    training_group = parser.add_argument_group("Training Parameters")
    training_group.add_argument(
        "--distributed", action="store_true", help="Use distributed training"
    )
    training_group.add_argument(
        "--epochs", type=int, default=3, help="Number of epochs"
    )
    training_group.add_argument(
        "--batch-size", type=int, default=4, help="Batch size"
    )
    training_group.add_argument(
        "--learning-rate", type=float, default=5e-5, help="Learning rate"
    )
    training_group.add_argument(
        "--checkpoint-interval",
        type=int,
        default=1,
        help="Interval for saving checkpoints",
    )
    
    early_stopping_group = parser.add_argument_group("Early Stopping Parameters")
    early_stopping_group.add_argument(
        "--early-stopping",
        action="store_true",
        help="Use early stopping",
    )
    early_stopping_group.add_argument(
        "--early-stop-patience",
        type=int,
        default=3,
        help="Patience for early stopping",
    )
    
    tuning_group = parser.add_argument_group("Hyperparameter Tuning Parameters")
    tuning_group.add_argument(
        "--tune-hyperparameters",
        action="store_true",
        help="Tune hyperparameters",
    )
    tuning_group.add_argument(
        "--n-trials",
        type=int,
        default=10,
        help="Number of trials for hyperparameter tuning",
    )
    
    mlflow_group = parser.add_argument_group("MLflow Parameters")
    mlflow_group.add_argument(
        "--no-mlflow", action="store_true", help="Disable MLflow logging"
    )
    mlflow_group.add_argument(
        "--experiment-name",
        type=str,
        default="rllm_training",
        help="MLflow experiment name",
    )
    mlflow_group.add_argument(
        "--run-name",
        type=str,
        help="MLflow run name",
    )
    
    misc_group = parser.add_argument_group("Miscellaneous Parameters")
    misc_group.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    misc_group.add_argument(
        "--sample-config",
        action="store_true",
        help="Generate a sample configuration file and exit",
    )
    misc_group.add_argument(
        "--kubernetes",
        action="store_true",
        help="Enable Kubernetes deployment integration",
    )
    
    args = parser.parse_args()
    
    if args.sample_config:
        config = get_deepcoder_config()
        
        config.training.num_epochs = 3
        config.training.batch_size = 4
        config.training.learning_rate = 5e-5
        config.training.early_stopping = True
        config.training.early_stop_patience = 3
        
        config.distributed = RLLMDistributedConfig(
            enabled=False,
            num_workers=4,
            resources_per_worker={"CPU": 2, "GPU": 0.5},
        )
        
        output_dir = args.output_dir or "./data/rllm"
        os.makedirs(output_dir, exist_ok=True)
        config_path = os.path.join(output_dir, "sample_config.json")
        
        with open(config_path, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
            
        print(f"Sample configuration file generated at {config_path}")
        return
    
    asyncio.run(
        train_on_historical_issues(
            config_path=args.config,
            benchmark_id=args.benchmark_id,
            train_path=args.train_path,
            val_path=args.val_path,
            output_dir=args.output_dir,
            distributed=args.distributed,
            log_to_mlflow=not args.no_mlflow,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            checkpoint_interval=args.checkpoint_interval,
            early_stopping=args.early_stopping,
            early_stop_patience=args.early_stop_patience,
            tune_hyperparameters=args.tune_hyperparameters,
            n_trials=args.n_trials,
            experiment_name=args.experiment_name,
            run_name=args.run_name,
            verbose=args.verbose,
        )
    )


if __name__ == "__main__":
    main()
