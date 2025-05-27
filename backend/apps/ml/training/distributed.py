"""
Distributed training for RLLM models.

This module provides functionality for distributed training of RLLM models
using Ray for parallelization.
"""

import os
import logging
import time
from typing import Dict, Any, Optional

from ..config.rllm_config import RLLMConfig, RLLMDistributedConfig


class DistributedTrainer:
    """Distributed trainer for RLLM models."""

    def __init__(
        self,
        config: Optional[RLLMConfig] = None,
        distributed_config: Optional[RLLMDistributedConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize trainer.

        Args:
            config: RLLM configuration
            distributed_config: Distributed training configuration
            logger: Logger
        """
        self.config = config or RLLMConfig()
        self.distributed_config = distributed_config or self.config.distributed
        self.logger = logger or logging.getLogger("DistributedTrainer")

        self.logger.info(
            f"Initialized distributed trainer with config: {self.distributed_config.model_dump()}"
        )

        self._initialize_ray()

    def _initialize_ray(self) -> None:
        """Initialize Ray for distributed training."""
        try:
            import ray

            if ray.is_initialized():
                self.logger.info("Ray is already initialized")
                return

            self.logger.info("Initializing Ray")

            ray.init(
                address=self.distributed_config.ray_address,
                ignore_reinit_error=True,
                logging_level=logging.INFO,
                log_to_driver=True,
                **self.distributed_config.ray_init_kwargs,
            )

            self.logger.info(
                f"Ray initialized with {ray.available_resources()}"
            )

        except ImportError:
            self.logger.error(
                "Ray not installed. Please install ray[tune] for distributed training."
            )
            raise
        except Exception as e:
            self.logger.error(f"Error initializing Ray: {e}")
            raise

    def train(
        self,
        train_data_path: str,
        val_data_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        num_epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        learning_rate: Optional[float] = None,
        num_workers: Optional[int] = None,
        use_tune: bool = False,
    ) -> Optional[str]:
        """
        Train model in distributed mode.

        Args:
            train_data_path: Path to training data
            val_data_path: Path to validation data
            output_dir: Output directory
            num_epochs: Number of epochs
            batch_size: Batch size
            learning_rate: Learning rate
            num_workers: Number of workers
            use_tune: Whether to use Ray Tune for hyperparameter tuning

        Returns:
            Path to trained model
        """
        try:
            from ray.train.torch import TorchTrainer
            from ray.train import ScalingConfig
            from ray.train.torch import TorchConfig

            num_epochs = num_epochs or self.config.training.num_epochs
            batch_size = batch_size or self.config.training.batch_size
            learning_rate = learning_rate or self.config.training.learning_rate
            num_workers = num_workers or self.distributed_config.num_workers
            output_dir = output_dir or self.config.model.output_dir

            self.logger.info(
                f"Starting distributed training with {num_workers} workers"
            )
            self.logger.info(f"Training data: {train_data_path}")
            self.logger.info(f"Validation data: {val_data_path}")
            self.logger.info(f"Output directory: {output_dir}")

            def train_func(config: Dict[str, Any]) -> None:
                """
                Training function for Ray.

                Args:
                    config: Configuration
                """
                from ray import train
                import torch
                import torch.optim as optim
                import transformers
                from transformers import AutoModelForCausalLM, AutoTokenizer
                from peft import (
                    get_peft_model,
                    LoraConfig,
                    prepare_model_for_kbit_training,
                )
                import numpy as np
                import json

                rank = train.get_context().get_world_rank()
                world_size = train.get_context().get_world_size()

                logging.basicConfig(
                    level=logging.INFO,
                    format=f"Worker {rank}/{world_size} - %(asctime)s - %(name)s - %(levelname)s - %(message)s",
                )
                logger = logging.getLogger(f"Worker-{rank}")

                logger.info(f"Starting worker {rank}/{world_size}")
                logger.info(f"Config: {config}")

                rllm_config = RLLMConfig()
                rllm_config.training.num_epochs = config["num_epochs"]
                rllm_config.training.batch_size = config["batch_size"]
                rllm_config.training.learning_rate = config["learning_rate"]
                rllm_config.model.model_id = config["model_id"]

                logger.info(f"Loading data from {config['train_data_path']}")

                with open(config["train_data_path"], "r") as f:
                    train_data = [json.loads(line) for line in f]

                train_data = train_data[rank::world_size]
                logger.info(
                    f"Worker {rank} loaded {len(train_data)} training examples"
                )

                val_data = None
                if config.get("val_data_path"):
                    logger.info(
                        f"Loading validation data from {config['val_data_path']}"
                    )
                    with open(config["val_data_path"], "r") as f:
                        val_data = [json.loads(line) for line in f]

                    val_data = val_data[rank::world_size]
                    logger.info(
                        f"Worker {rank} loaded {len(val_data)} validation examples"
                    )

                logger.info(f"Initializing model {config['model_id']}")

                tokenizer = AutoTokenizer.from_pretrained(
                    config["model_id"],
                    trust_remote_code=True,
                )

                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token

                quantization_config = {}
                if config.get("load_in_8bit", False):
                    quantization_config["load_in_8bit"] = True
                elif config.get("load_in_4bit", False):
                    quantization_config["load_in_4bit"] = True
                    quantization_config["bnb_4bit_compute_dtype"] = (
                        torch.float16
                    )
                    quantization_config["bnb_4bit_quant_type"] = "nf4"
                    quantization_config["bnb_4bit_use_double_quant"] = True

                model = AutoModelForCausalLM.from_pretrained(
                    config["model_id"],
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    **quantization_config,
                )

                if config.get("use_lora", False):
                    logger.info("Applying LoRA")

                    if quantization_config:
                        model = prepare_model_for_kbit_training(model)

                    lora_config = LoraConfig(
                        r=config.get("lora_r", 16),
                        lora_alpha=config.get("lora_alpha", 32),
                        lora_dropout=config.get("lora_dropout", 0.05),
                        bias="none",
                        task_type="CAUSAL_LM",
                        target_modules=config.get(
                            "lora_target_modules", ["q_proj", "v_proj"]
                        ),
                    )

                    model = get_peft_model(model, lora_config)

                model.train()
                if hasattr(model, "gradient_checkpointing_enable"):
                    model.gradient_checkpointing_enable()

                optimizer = optim.AdamW(
                    model.parameters(),
                    lr=config["learning_rate"],
                    weight_decay=config.get("weight_decay", 0.01),
                )

                scheduler = transformers.get_scheduler(
                    "cosine",
                    optimizer=optimizer,
                    num_warmup_steps=int(
                        0.1
                        * config["num_epochs"]
                        * len(train_data)
                        / config["batch_size"]
                    ),
                    num_training_steps=config["num_epochs"]
                    * len(train_data)
                    / config["batch_size"],
                )

                logger.info("Starting training loop")

                for epoch in range(config["num_epochs"]):
                    logger.info(
                        f"Starting epoch {epoch + 1}/{config['num_epochs']}"
                    )

                    np.random.shuffle(train_data)

                    num_batches = len(train_data) // config["batch_size"]
                    if len(train_data) % config["batch_size"] != 0:
                        num_batches += 1

                    total_loss = 0.0

                    for batch_idx in range(num_batches):
                        batch_start = batch_idx * config["batch_size"]
                        batch_end = min(
                            batch_start + config["batch_size"], len(train_data)
                        )
                        batch = train_data[batch_start:batch_end]

                        input_texts = [
                            example["input_text"] for example in batch
                        ]
                        output_texts = [
                            example["output_text"] for example in batch
                        ]
                        rewards = torch.tensor(
                            [example["reward"] for example in batch],
                            dtype=torch.float32,
                        )

                        inputs = tokenizer(
                            input_texts,
                            padding=True,
                            truncation=True,
                            return_tensors="pt",
                            max_length=config.get("max_length", 2048),
                        ).to(model.device)

                        outputs = tokenizer(
                            output_texts,
                            padding=True,
                            truncation=True,
                            return_tensors="pt",
                            max_length=config.get("max_length", 2048),
                        ).to(model.device)

                        model_outputs = model(
                            input_ids=inputs["input_ids"],
                            attention_mask=inputs["attention_mask"],
                            labels=outputs["input_ids"],
                        )

                        loss = model_outputs.loss

                        if config.get("use_rewards", True):
                            scaled_rewards = 0.1 + 1.9 * (
                                rewards - rewards.min()
                            ) / (rewards.max() - rewards.min() + 1e-8)
                            scaled_rewards = scaled_rewards.to(model.device)

                            loss = loss * scaled_rewards.mean()

                        loss.backward()

                        if config.get("max_grad_norm", 0) > 0:
                            torch.nn.utils.clip_grad_norm_(
                                model.parameters(),
                                config.get("max_grad_norm", 1.0),
                            )

                        optimizer.step()
                        scheduler.step()
                        optimizer.zero_grad()

                        total_loss += loss.item()

                        if (
                            batch_idx + 1
                        ) % 10 == 0 or batch_idx == num_batches - 1:
                            logger.info(
                                f"Epoch {epoch + 1}/{config['num_epochs']}, "
                                f"Batch {batch_idx + 1}/{num_batches}, "
                                f"Loss: {loss.item():.4f}, "
                                f"LR: {scheduler.get_last_lr()[0]:.8f}"
                            )

                            train.report(
                                {
                                    "epoch": epoch + 1,
                                    "batch": batch_idx + 1,
                                    "loss": loss.item(),
                                    "learning_rate": scheduler.get_last_lr()[
                                        0
                                    ],
                                }
                            )

                    avg_loss = total_loss / num_batches
                    logger.info(
                        f"Epoch {epoch + 1}/{config['num_epochs']} completed, Average Loss: {avg_loss:.4f}"
                    )

                    if val_data:
                        logger.info("Evaluating on validation data")

                        model.eval()
                        val_loss = 0.0

                        with torch.no_grad():
                            val_num_batches = (
                                len(val_data) // config["batch_size"]
                            )
                            if len(val_data) % config["batch_size"] != 0:
                                val_num_batches += 1

                            for batch_idx in range(val_num_batches):
                                batch_start = batch_idx * config["batch_size"]
                                batch_end = min(
                                    batch_start + config["batch_size"],
                                    len(val_data),
                                )
                                batch = val_data[batch_start:batch_end]

                                input_texts = [
                                    example["input_text"] for example in batch
                                ]
                                output_texts = [
                                    example["output_text"] for example in batch
                                ]

                                inputs = tokenizer(
                                    input_texts,
                                    padding=True,
                                    truncation=True,
                                    return_tensors="pt",
                                    max_length=config.get("max_length", 2048),
                                ).to(model.device)

                                outputs = tokenizer(
                                    output_texts,
                                    padding=True,
                                    truncation=True,
                                    return_tensors="pt",
                                    max_length=config.get("max_length", 2048),
                                ).to(model.device)

                                model_outputs = model(
                                    input_ids=inputs["input_ids"],
                                    attention_mask=inputs["attention_mask"],
                                    labels=outputs["input_ids"],
                                )

                                batch_loss = model_outputs.loss.item()
                                val_loss += batch_loss

                        avg_val_loss = val_loss / val_num_batches
                        logger.info(f"Validation Loss: {avg_val_loss:.4f}")

                        train.report(
                            {
                                "epoch": epoch + 1,
                                "val_loss": avg_val_loss,
                            }
                        )

                        model.train()

                logger.info(f"Saving model to {config['output_dir']}")

                os.makedirs(config["output_dir"], exist_ok=True)

                model.save_pretrained(config["output_dir"])

                tokenizer.save_pretrained(config["output_dir"])

                with open(
                    os.path.join(config["output_dir"], "rllm_config.json"), "w"
                ) as f:
                    json.dump(rllm_config.model_dump(), f, indent=2)

                logger.info("Training completed successfully")

            scaling_config = ScalingConfig(
                num_workers=num_workers,
                use_gpu=self.distributed_config.use_gpu,
                resources_per_worker=self.distributed_config.resources_per_worker,
            )

            torch_config = TorchConfig(
                backend=self.distributed_config.backend,
            )

            trainer = TorchTrainer(
                train_loop_per_worker=train_func,
                train_loop_config={
                    "train_data_path": train_data_path,
                    "val_data_path": val_data_path,
                    "output_dir": output_dir,
                    "num_epochs": num_epochs,
                    "batch_size": batch_size,
                    "learning_rate": learning_rate,
                    "model_id": self.config.model.model_id,
                    "use_lora": self.config.model.use_lora,
                    "lora_r": self.config.model.lora_r,
                    "lora_alpha": self.config.model.lora_alpha,
                    "lora_dropout": self.config.model.lora_dropout,
                    "lora_target_modules": self.config.model.lora_target_modules,
                    "load_in_8bit": self.config.model.load_in_8bit,
                    "load_in_4bit": self.config.model.load_in_4bit,
                    "max_length": self.config.training.max_length,
                    "weight_decay": self.config.training.weight_decay,
                    "max_grad_norm": self.config.training.max_grad_norm,
                    "use_rewards": True,
                },
                scaling_config=scaling_config,
                torch_config=torch_config,
            )

            result = trainer.fit()

            self.logger.info(f"Training completed with result: {result}")

            return output_dir

        except ImportError as e:
            self.logger.error(f"Required package not installed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error in distributed training: {e}")
            raise

    def tune(
        self,
        train_data_path: str,
        val_data_path: str,
        output_dir: Optional[str] = None,
        num_samples: int = 10,
        max_concurrent_trials: int = 2,
    ) -> Optional[str]:
        """
        Tune hyperparameters using Ray Tune.

        Args:
            train_data_path: Path to training data
            val_data_path: Path to validation data
            output_dir: Output directory
            num_samples: Number of samples
            max_concurrent_trials: Maximum number of concurrent trials

        Returns:
            Path to best model
        """
        try:
            from ray import tune
            from ray.tune.search.optuna import OptunaSearch

            output_dir = output_dir or self.config.model.output_dir

            self.logger.info(
                f"Starting hyperparameter tuning with {num_samples} samples"
            )
            self.logger.info(f"Training data: {train_data_path}")
            self.logger.info(f"Validation data: {val_data_path}")
            self.logger.info(f"Output directory: {output_dir}")

            search_space = {
                "learning_rate": tune.loguniform(1e-6, 1e-4),
                "batch_size": tune.choice([4, 8, 16]),
                "num_epochs": tune.choice([1, 2, 3]),
                "weight_decay": tune.loguniform(0.01, 0.1),
                "lora_r": tune.choice([8, 16, 32]),
                "lora_alpha": tune.choice([16, 32, 64]),
                "lora_dropout": tune.uniform(0.0, 0.1),
            }

            search_alg = OptunaSearch()

            tuner = tune.Tuner(
                trainable=lambda config: self.train(
                    train_data_path=train_data_path,
                    val_data_path=val_data_path,
                    output_dir=os.path.join(
                        output_dir, f"trial_{time.time()}"
                    ),
                    num_epochs=config["num_epochs"],
                    batch_size=config["batch_size"],
                    learning_rate=config["learning_rate"],
                    num_workers=self.distributed_config.num_workers,
                ),
                param_space=search_space,
                tune_config=tune.TuneConfig(
                    metric="val_loss",
                    mode="min",
                    num_samples=num_samples,
                    max_concurrent_trials=max_concurrent_trials,
                    search_alg=search_alg,
                ),
            )

            results = tuner.fit()

            best_result = results.get_best_result(
                metric="val_loss", mode="min"
            )

            self.logger.info(f"Best hyperparameters: {best_result.config}")
            self.logger.info(
                f"Best validation loss: {best_result.metrics['val_loss']}"
            )

            final_output_dir = os.path.join(output_dir, "best_model")

            self.train(
                train_data_path=train_data_path,
                val_data_path=val_data_path,
                output_dir=final_output_dir,
                num_epochs=best_result.config["num_epochs"],
                batch_size=best_result.config["batch_size"],
                learning_rate=best_result.config["learning_rate"],
                num_workers=self.distributed_config.num_workers,
            )

            return final_output_dir

        except ImportError as e:
            self.logger.error(f"Required package not installed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error in hyperparameter tuning: {e}")
            raise
