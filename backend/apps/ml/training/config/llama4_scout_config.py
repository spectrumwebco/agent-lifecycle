"""
Llama 4 Scout Training Configuration

This module defines the configuration for fine-tuning the Llama 4 Scout model
on GitOps, Terraform, and Kubernetes issue data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any


@dataclass
class Llama4ScoutConfig:
    """Configuration for Llama 4 Scout fine-tuning."""

    model_name: str = "meta-llama/llama-4-scout"
    model_revision: str = "main"
    tokenizer_name: str = "meta-llama/llama-4-scout"
    tokenizer_revision: str = "main"

    learning_rate: float = 1e-5
    weight_decay: float = 0.01
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8
    max_grad_norm: float = 1.0

    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 8
    eval_accumulation_steps: int = 8

    max_seq_length: int = 4096

    optim: str = "adamw_torch"
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.1

    fp16: bool = True
    bf16: bool = False

    save_strategy: str = "steps"
    save_steps: int = 500
    save_total_limit: int = 3

    evaluation_strategy: str = "steps"
    eval_steps: int = 500

    logging_dir: str = "logs"
    logging_strategy: str = "steps"
    logging_steps: int = 100

    output_dir: str = "models/llama4-scout-fine-tuned"

    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])

    enable_trajectory_tracking: bool = True
    trajectory_output_dir: str = "trajectories/llama4-scout"

    swe_agent_compatible: bool = True

    dataset_name: str = "gitops-terraform-k8s-issues"
    dataset_config_name: str = "solved_issues"

    mlflow_tracking_uri: Optional[str] = None
    mlflow_experiment_name: str = "llama4-scout-fine-tuning"

    kubeflow_pipeline_name: str = "llama4-scout-fine-tuning-pipeline"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Llama4ScoutConfig":
        """Create a configuration from a dictionary."""
        return cls(**config_dict)


@dataclass
class Llama4ScoutTrainingArguments:
    """Training arguments for Llama 4 Scout fine-tuning."""

    config: Llama4ScoutConfig = field(default_factory=Llama4ScoutConfig)

    def to_transformers_training_arguments(self) -> Dict[str, Any]:
        """Convert to transformers TrainingArguments format."""
        config_dict = self.config.to_dict()
        training_args = {
            "learning_rate": config_dict["learning_rate"],
            "weight_decay": config_dict["weight_decay"],
            "adam_beta1": config_dict["adam_beta1"],
            "adam_beta2": config_dict["adam_beta2"],
            "adam_epsilon": config_dict["adam_epsilon"],
            "max_grad_norm": config_dict["max_grad_norm"],
            "num_train_epochs": config_dict["num_train_epochs"],
            "per_device_train_batch_size": config_dict["per_device_train_batch_size"],
            "per_device_eval_batch_size": config_dict["per_device_eval_batch_size"],
            "gradient_accumulation_steps": config_dict["gradient_accumulation_steps"],
            "eval_accumulation_steps": config_dict["eval_accumulation_steps"],
            "optim": config_dict["optim"],
            "lr_scheduler_type": config_dict["lr_scheduler_type"],
            "warmup_ratio": config_dict["warmup_ratio"],
            "fp16": config_dict["fp16"],
            "bf16": config_dict["bf16"],
            "save_strategy": config_dict["save_strategy"],
            "save_steps": config_dict["save_steps"],
            "save_total_limit": config_dict["save_total_limit"],
            "evaluation_strategy": config_dict["evaluation_strategy"],
            "eval_steps": config_dict["eval_steps"],
            "logging_dir": config_dict["logging_dir"],
            "logging_strategy": config_dict["logging_strategy"],
            "logging_steps": config_dict["logging_steps"],
            "output_dir": config_dict["output_dir"],
        }
        return training_args


def get_default_config() -> Llama4ScoutConfig:
    """Get the default configuration for Llama 4 Scout fine-tuning."""
    return Llama4ScoutConfig()
