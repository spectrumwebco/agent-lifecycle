"""
Configuration for RLLM models and training.

This module provides configuration classes for RLLM models and training,
supporting different model sizes and training regimes.
"""

import json
from typing import Dict, List, Any
from pydantic import BaseModel, Field


class RLLMModelConfig(BaseModel):
    """Configuration for RLLM models."""

    model_id: str = Field(
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        description="Base model ID",
    )
    output_dir: str = Field("./outputs/rllm", description="Output directory")
    max_seq_length: int = Field(8192, description="Maximum sequence length")
    use_lora: bool = Field(True, description="Whether to use LoRA")
    lora_r: int = Field(16, description="LoRA r parameter")
    lora_alpha: int = Field(32, description="LoRA alpha parameter")
    lora_dropout: float = Field(0.05, description="LoRA dropout")
    use_8bit_quantization: bool = Field(
        False, description="Whether to use 8-bit quantization"
    )
    use_4bit_quantization: bool = Field(
        True, description="Whether to use 4-bit quantization"
    )
    seed: int = Field(42, description="Random seed")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def save_to_json(self, path: str) -> None:
        """Save to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "RLLMModelConfig":
        """Load from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)

    def get_lora_config(self) -> Dict[str, Any]:
        """Get LoRA configuration."""
        return {
            "r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "bias": "none",
            "task_type": "CAUSAL_LM",
            "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
        }

    def get_quantization_config(self) -> Dict[str, Any]:
        """Get quantization configuration."""
        if self.use_8bit_quantization:
            return {"load_in_8bit": True}
        elif self.use_4bit_quantization:
            return {
                "load_in_4bit": True,
                "bnb_4bit_compute_dtype": "float16",
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_use_double_quant": True,
            }
        else:
            return {}


class RLLMTrainingConfig(BaseModel):
    """Configuration for RLLM training."""

    learning_rate: float = Field(5e-5, description="Learning rate")
    num_train_epochs: int = Field(3, description="Number of training epochs")
    per_device_train_batch_size: int = Field(
        1, description="Per device training batch size"
    )
    per_device_eval_batch_size: int = Field(
        1, description="Per device evaluation batch size"
    )
    gradient_accumulation_steps: int = Field(
        16, description="Gradient accumulation steps"
    )
    warmup_steps: int = Field(100, description="Warmup steps")
    weight_decay: float = Field(0.01, description="Weight decay")
    logging_steps: int = Field(10, description="Logging steps")
    save_steps: int = Field(500, description="Save steps")
    eval_steps: int = Field(500, description="Evaluation steps")
    save_total_limit: int = Field(3, description="Save total limit")
    fp16: bool = Field(True, description="Whether to use fp16")
    bf16: bool = Field(False, description="Whether to use bf16")
    optim: str = Field("adamw_torch", description="Optimizer")
    lr_scheduler_type: str = Field(
        "cosine", description="Learning rate scheduler type"
    )
    max_grad_norm: float = Field(1.0, description="Maximum gradient norm")
    report_to: List[str] = Field(["mlflow"], description="Report to")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def save_to_json(self, path: str) -> None:
        """Save to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "RLLMTrainingConfig":
        """Load from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)


class RLLMDistributedConfig(BaseModel):
    """Configuration for distributed training."""

    use_ray: bool = Field(True, description="Whether to use Ray")
    num_workers: int = Field(4, description="Number of workers")
    num_gpus_per_worker: int = Field(
        1, description="Number of GPUs per worker"
    )
    num_cpus_per_worker: int = Field(
        4, description="Number of CPUs per worker"
    )
    memory_per_worker: int = Field(16, description="Memory per worker in GB")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def save_to_json(self, path: str) -> None:
        """Save to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "RLLMDistributedConfig":
        """Load from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)


class RLLMRewardConfig(BaseModel):
    """Configuration for RLLM rewards."""

    bug_fix_reward: float = Field(1.0, description="Reward for fixing bugs")
    feature_implementation_reward: float = Field(
        1.0, description="Reward for implementing features"
    )
    documentation_reward: float = Field(
        0.8, description="Reward for documentation"
    )
    code_quality_weight: float = Field(
        0.3, description="Weight for code quality"
    )
    code_readability_weight: float = Field(
        0.3, description="Weight for code readability"
    )
    test_coverage_weight: float = Field(
        0.3, description="Weight for test coverage"
    )
    completion_time_weight: float = Field(
        0.2, description="Weight for completion time"
    )
    use_kl_penalty: bool = Field(True, description="Whether to use KL penalty")
    kl_penalty_weight: float = Field(0.1, description="Weight for KL penalty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def save_to_json(self, path: str) -> None:
        """Save to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "RLLMRewardConfig":
        """Load from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)


class RLLMConfig(BaseModel):
    """Configuration for RLLM."""

    model: RLLMModelConfig = Field(
        default_factory=RLLMModelConfig, description="Model configuration"
    )
    training: RLLMTrainingConfig = Field(
        default_factory=RLLMTrainingConfig,
        description="Training configuration",
    )
    distributed: RLLMDistributedConfig = Field(
        default_factory=RLLMDistributedConfig,
        description="Distributed configuration",
    )
    reward: RLLMRewardConfig = Field(
        default_factory=RLLMRewardConfig, description="Reward configuration"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def save_to_json(self, path: str) -> None:
        """Save to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "RLLMConfig":
        """Load from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)


def get_default_config() -> RLLMConfig:
    """Get default configuration."""
    return RLLMConfig()


def get_deepcoder_config() -> RLLMConfig:
    """Get configuration for DeepCoder."""
    config = RLLMConfig()
    config.model.model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"
    config.model.max_seq_length = 16384
    config.training.learning_rate = 1e-5
    config.training.num_train_epochs = 5
    config.distributed.num_workers = 8
    config.distributed.num_gpus_per_worker = 4
    config.reward.code_quality_weight = 0.4
    config.reward.test_coverage_weight = 0.4
    return config


def get_config_for_model(model_type: str) -> RLLMConfig:
    """
    Get configuration for model type.

    Args:
        model_type: Model type

    Returns:
        Configuration
    """
    if model_type == "deepcoder":
        return get_deepcoder_config()
    else:
        return get_default_config()
