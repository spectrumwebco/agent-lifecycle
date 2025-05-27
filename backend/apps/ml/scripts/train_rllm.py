"""
Train RLLM models on historical issue trajectories.

This script demonstrates how to use the RLLM framework to train models
on historical issue trajectories from GitHub and Gitee.
"""

import os
import argparse
import asyncio
import logging
from typing import Optional
from datetime import datetime

from ..config.rllm_config import RLLMConfig, get_deepcoder_config
from ..training.trainer import RLLMTrainer
from ..integration.benchmark_integration import BenchmarkIntegration
from ..integration.ml_integration import MLIntegration


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
):
    """
    Train RLLM model on historical issues.

    Args:
        config_path: Path to configuration file
        benchmark_id: Benchmark ID to use for training
        train_path: Path to training data
        val_path: Path to validation data
        output_dir: Output directory
        distributed: Whether to use distributed training
        log_to_mlflow: Whether to log to MLflow
        num_epochs: Number of epochs
        batch_size: Batch size
        learning_rate: Learning rate
    """
    logger = logging.getLogger("train_rllm")

    if config_path and os.path.exists(config_path):
        config = RLLMConfig.from_json(config_path)
        logger.info(f"Loaded configuration from {config_path}")
    else:
        config = get_deepcoder_config()
        logger.info("Using default DeepCoder configuration")

    config.training.num_epochs = num_epochs
    config.training.batch_size = batch_size
    config.training.learning_rate = learning_rate

    os.makedirs(output_dir, exist_ok=True)

    benchmark_integration = BenchmarkIntegration(
        config=config,
        output_dir=output_dir,
        logger=logger,
    )

    # trajectory_integration = TrajectoryIntegration(
    #     config=config,
    #     output_dir=output_dir,
    #     logger=logger,
    # )

    ml_integration = MLIntegration(
        config=config,
        logger=logger,
    )

    if log_to_mlflow:
        await ml_integration.setup_mlflow(experiment_name="rllm_training")

    if train_path is None and benchmark_id is not None:
        result_path, train_path, val_path = (
            await benchmark_integration.convert_existing_benchmark(
                benchmark_id=benchmark_id,
            )
        )

        if train_path is None:
            logger.error(f"Failed to convert benchmark {benchmark_id}")
            return

    if train_path is None:
        logger.error("No training data provided")
        return

    logger.info(f"Using training data: {train_path}")
    if val_path:
        logger.info(f"Using validation data: {val_path}")

    trainer = RLLMTrainer(
        config=config,
        logger=logger,
    )

    run_id = f"rllm_{int(datetime.now().timestamp())}"

    if log_to_mlflow:
        mlflow_run_id = await ml_integration.log_training_start(
            run_id=run_id,
            config=config.model_dump(),
        )

    model_path = await trainer.train(
        train_data_path=train_path,
        val_data_path=val_path,
        output_dir=output_dir,
        distributed=distributed,
        num_epochs=num_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
    )

    if model_path:
        logger.info(f"Model saved to {model_path}")

        if log_to_mlflow:
            metrics = {
                "training_completed": 1.0,
            }

            await ml_integration.log_training_end(
                run_id=mlflow_run_id,
                metrics=metrics,
                artifacts=[model_path],
            )
    else:
        logger.error("Training failed")


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(
        description="Train RLLM model on historical issues"
    )
    parser.add_argument(
        "--config", type=str, help="Path to configuration file"
    )
    parser.add_argument(
        "--benchmark-id", type=str, help="Benchmark ID to use for training"
    )
    parser.add_argument("--train-path", type=str, help="Path to training data")
    parser.add_argument("--val-path", type=str, help="Path to validation data")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/rllm",
        help="Output directory",
    )
    parser.add_argument(
        "--distributed", action="store_true", help="Use distributed training"
    )
    parser.add_argument(
        "--no-mlflow", action="store_true", help="Disable MLflow logging"
    )
    parser.add_argument(
        "--epochs", type=int, default=3, help="Number of epochs"
    )
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument(
        "--learning-rate", type=float, default=5e-5, help="Learning rate"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

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
        )
    )


if __name__ == "__main__":
    main()
