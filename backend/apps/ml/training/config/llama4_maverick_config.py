"""
Configuration for fine-tuning Llama 4 Maverick model.
"""

import os
from typing import Dict, Any, List, Optional, Union


class Llama4MaverickConfig:
    """
    Configuration for fine-tuning Llama 4 Maverick model.
    """

    def __init__(
        self,
        model_id: str = "meta-llama/llama-4-maverick",
        output_dir: str = "/models/llama4-maverick",
        train_file: str = "/data/train.json",
        validation_file: str = "/data/validation.json",
        test_file: Optional[str] = "/data/test.json",
        max_seq_length: int = 4096,
        learning_rate: float = 5e-5,
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 8,
        per_device_eval_batch_size: int = 8,
        gradient_accumulation_steps: int = 4,
        warmup_steps: int = 500,
        weight_decay: float = 0.01,
        logging_steps: int = 100,
        evaluation_strategy: str = "steps",
        eval_steps: int = 500,
        save_steps: int = 1000,
        save_total_limit: int = 3,
        fp16: bool = True,
        bf16: bool = False,
        load_best_model_at_end: bool = True,
        metric_for_best_model: str = "eval_loss",
        greater_is_better: bool = False,
        seed: int = 42,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        use_lora: bool = True,
        use_8bit_quantization: bool = False,
        use_4bit_quantization: bool = False,
    ):
        """
        Initialize Llama 4 Maverick configuration.

        Args:
            model_id: Model ID
            output_dir: Output directory
            train_file: Training file
            validation_file: Validation file
            test_file: Test file
            max_seq_length: Maximum sequence length
            learning_rate: Learning rate
            num_train_epochs: Number of training epochs
            per_device_train_batch_size: Per device training batch size
            per_device_eval_batch_size: Per device evaluation batch size
            gradient_accumulation_steps: Gradient accumulation steps
            warmup_steps: Warmup steps
            weight_decay: Weight decay
            logging_steps: Logging steps
            evaluation_strategy: Evaluation strategy
            eval_steps: Evaluation steps
            save_steps: Save steps
            save_total_limit: Save total limit
            fp16: Use FP16
            bf16: Use BF16
            load_best_model_at_end: Load best model at end
            metric_for_best_model: Metric for best model
            greater_is_better: Greater is better
            seed: Random seed
            lora_r: LoRA r
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            use_lora: Use LoRA
            use_8bit_quantization: Use 8-bit quantization
            use_4bit_quantization: Use 4-bit quantization
        """
        self.model_id = model_id
        self.output_dir = output_dir
        self.train_file = train_file
        self.validation_file = validation_file
        self.test_file = test_file
        self.max_seq_length = max_seq_length
        self.learning_rate = learning_rate
        self.num_train_epochs = num_train_epochs
        self.per_device_train_batch_size = per_device_train_batch_size
        self.per_device_eval_batch_size = per_device_eval_batch_size
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.warmup_steps = warmup_steps
        self.weight_decay = weight_decay
        self.logging_steps = logging_steps
        self.evaluation_strategy = evaluation_strategy
        self.eval_steps = eval_steps
        self.save_steps = save_steps
        self.save_total_limit = save_total_limit
        self.fp16 = fp16
        self.bf16 = bf16
        self.load_best_model_at_end = load_best_model_at_end
        self.metric_for_best_model = metric_for_best_model
        self.greater_is_better = greater_is_better
        self.seed = seed
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.use_lora = use_lora
        self.use_8bit_quantization = use_8bit_quantization
        self.use_4bit_quantization = use_4bit_quantization

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "model_id": self.model_id,
            "output_dir": self.output_dir,
            "train_file": self.train_file,
            "validation_file": self.validation_file,
            "test_file": self.test_file,
            "max_seq_length": self.max_seq_length,
            "learning_rate": self.learning_rate,
            "num_train_epochs": self.num_train_epochs,
            "per_device_train_batch_size": self.per_device_train_batch_size,
            "per_device_eval_batch_size": self.per_device_eval_batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "warmup_steps": self.warmup_steps,
            "weight_decay": self.weight_decay,
            "logging_steps": self.logging_steps,
            "evaluation_strategy": self.evaluation_strategy,
            "eval_steps": self.eval_steps,
            "save_steps": self.save_steps,
            "save_total_limit": self.save_total_limit,
            "fp16": self.fp16,
            "bf16": self.bf16,
            "load_best_model_at_end": self.load_best_model_at_end,
            "metric_for_best_model": self.metric_for_best_model,
            "greater_is_better": self.greater_is_better,
            "seed": self.seed,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "use_lora": self.use_lora,
            "use_8bit_quantization": self.use_8bit_quantization,
            "use_4bit_quantization": self.use_4bit_quantization,
        }

    def get_training_args(self) -> Dict[str, Any]:
        """
        Get training arguments.

        Returns:
            Training arguments
        """
        return {
            "output_dir": self.output_dir,
            "learning_rate": self.learning_rate,
            "num_train_epochs": self.num_train_epochs,
            "per_device_train_batch_size": self.per_device_train_batch_size,
            "per_device_eval_batch_size": self.per_device_eval_batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "warmup_steps": self.warmup_steps,
            "weight_decay": self.weight_decay,
            "logging_steps": self.logging_steps,
            "evaluation_strategy": self.evaluation_strategy,
            "eval_steps": self.eval_steps,
            "save_steps": self.save_steps,
            "save_total_limit": self.save_total_limit,
            "fp16": self.fp16,
            "bf16": self.bf16,
            "load_best_model_at_end": self.load_best_model_at_end,
            "metric_for_best_model": self.metric_for_best_model,
            "greater_is_better": self.greater_is_better,
            "seed": self.seed,
        }

    def get_lora_config(self) -> Dict[str, Any]:
        """
        Get LoRA configuration.

        Returns:
            LoRA configuration
        """
        if not self.use_lora:
            return {}

        return {
            "r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "bias": "none",
            "task_type": "CAUSAL_LM",
        }

    def get_quantization_config(self) -> Dict[str, Any]:
        """
        Get quantization configuration.

        Returns:
            Quantization configuration
        """
        if self.use_8bit_quantization:
            return {"load_in_8bit": True}
        elif self.use_4bit_quantization:
            return {"load_in_4bit": True}
        else:
            return {}

    def save_to_json(self, file_path: str) -> None:
        """
        Save configuration to JSON file.

        Args:
            file_path: File path
        """
        import json

        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, file_path: str) -> "Llama4MaverickConfig":
        """
        Load configuration from JSON file.

        Args:
            file_path: File path

        Returns:
            Configuration
        """
        import json

        with open(file_path, "r") as f:
            config_dict = json.load(f)

        return cls(**config_dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Llama4MaverickConfig":
        """
        Load configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Configuration
        """
        return cls(**config_dict)


class Llama4ScoutConfig(Llama4MaverickConfig):
    """
    Configuration for fine-tuning Llama 4 Scout model.
    """

    def __init__(
        self,
        model_id: str = "meta-llama/llama-4-scout",
        output_dir: str = "/models/llama4-scout",
        **kwargs,
    ):
        """
        Initialize Llama 4 Scout configuration.

        Args:
            model_id: Model ID
            output_dir: Output directory
            **kwargs: Additional arguments
        """
        super().__init__(model_id=model_id, output_dir=output_dir, **kwargs)


def get_default_maverick_config() -> Llama4MaverickConfig:
    """
    Get default Llama 4 Maverick configuration.

    Returns:
        Default configuration
    """
    return Llama4MaverickConfig()


def get_default_scout_config() -> Llama4ScoutConfig:
    """
    Get default Llama 4 Scout configuration.

    Returns:
        Default configuration
    """
    return Llama4ScoutConfig()


def get_config_for_model(
    model_type: str,
) -> Union[Llama4MaverickConfig, Llama4ScoutConfig]:
    """
    Get configuration for model.

    Args:
        model_type: Model type

    Returns:
        Configuration
    """
    if model_type == "llama4-maverick":
        return get_default_maverick_config()
    elif model_type == "llama4-scout":
        return get_default_scout_config()
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
