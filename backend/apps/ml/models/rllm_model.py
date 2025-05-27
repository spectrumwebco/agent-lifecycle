"""
RLLM model wrapper and integration.

This module provides a wrapper for RLLM models and integration with the
existing ML infrastructure.
"""

import os
import logging
from typing import Optional, Dict, List, Union, Any
import torch

from ..config.rllm_config import RLLMModelConfig, RLLMConfig
from ..rust_bindings import get_fast_tokenizer


class RLLMModel:
    """Wrapper for RLLM models."""
    
    fast_tokenize = get_fast_tokenizer()

    def __init__(
        self,
        model_config: Optional[RLLMModelConfig] = None,
        device: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize model.

        Args:
            model_config: Model configuration
            device: Device to use
            logger: Logger
        """
        self.model_config = model_config or RLLMModelConfig()
        self.device = device or (
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.logger = logger or logging.getLogger("RLLMModel")

        self.model = None
        self.tokenizer = None

        self.logger.info(
            f"Initialized RLLM model with config: {self.model_config.model_id}"
        )
        self.logger.info(f"Using device: {self.device}")
        
        if self.fast_tokenize:
            self.logger.info("Using Rust implementation for tokenization")
        else:
            self.logger.info("Using Python implementation for tokenization")

    def load_model(self) -> None:
        """Load model."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import (
                get_peft_model,
                LoraConfig,
                prepare_model_for_kbit_training,
            )

            self.logger.info(f"Loading model: {self.model_config.model_id}")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_config.model_id,
                trust_remote_code=True,
            )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            quantization_config = self.model_config.get_quantization_config()

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_config.model_id,
                torch_dtype=torch.float16,
                device_map=self.device,
                trust_remote_code=True,
                **quantization_config,
            )

            if self.model_config.use_lora:
                self.logger.info("Applying LoRA")

                if quantization_config:
                    self.model = prepare_model_for_kbit_training(self.model)

                lora_config = LoraConfig(**self.model_config.get_lora_config())

                self.model = get_peft_model(self.model, lora_config)

            self.logger.info("Model loaded successfully")

        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise

    def save_model(self, output_dir: Optional[str] = None) -> Optional[str]:
        """
        Save model.

        Args:
            output_dir: Output directory

        Returns:
            Path to saved model
        """
        if self.model is None:
            self.logger.error("Model not loaded")
            return None

        output_dir = output_dir or self.model_config.output_dir
        os.makedirs(output_dir, exist_ok=True)

        try:
            self.logger.info(f"Saving model to {output_dir}")

            if self.model is not None:
                self.model.save_pretrained(output_dir)

            if self.tokenizer is not None:
                self.tokenizer.save_pretrained(output_dir)

            config_path = os.path.join(output_dir, "rllm_config.json")
            self.model_config.save_to_json(config_path)

            self.logger.info("Model saved successfully")

            return output_dir

        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
            return None

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
        if self.model is None or self.tokenizer is None:
            self.logger.error("Model or tokenizer not loaded")
            return None

        try:
            if self.fast_tokenize:
                inputs = self.fast_tokenize(
                    self.tokenizer,
                    prompt,
                    padding=True,
                    truncation=True,
                    max_length=self.model_config.max_length or 512,
                    return_tensors="pt"
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            else:
                inputs = self.tokenizer(prompt, return_tensors="pt").to(
                    self.device
                )

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
            )

            generated_text = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )

            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt) :]

            return generated_text.strip()

        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            return None

    def prepare_for_training(self) -> None:
        """Prepare model for training."""
        if self.model is None:
            self.logger.error("Model not loaded")
            return

        try:
            self.logger.info("Preparing model for training")

            self.model.train()

            if hasattr(self.model, "gradient_checkpointing_enable"):
                self.model.gradient_checkpointing_enable()

            self.logger.info("Model prepared for training")

        except Exception as e:
            self.logger.error(f"Error preparing model for training: {e}")
            raise

    def prepare_for_inference(self) -> None:
        """Prepare model for inference."""
        if self.model is None:
            self.logger.error("Model not loaded")
            return

        try:
            self.logger.info("Preparing model for inference")

            self.model.eval()

            self.logger.info("Model prepared for inference")

        except Exception as e:
            self.logger.error(f"Error preparing model for inference: {e}")
            raise

    @classmethod
    def from_pretrained(
        cls, model_path: str, device: Optional[str] = None
    ) -> Optional["RLLMModel"]:
        """
        Load model from pretrained.

        Args:
            model_path: Path to model
            device: Device to use

        Returns:
            Model
        """
        logger = logging.getLogger("RLLMModel")

        try:
            logger.info(f"Loading model from {model_path}")

            config_path = os.path.join(model_path, "rllm_config.json")
            if os.path.exists(config_path):
                model_config = RLLMModelConfig.from_json(config_path)
            else:
                logger.warning(
                    f"Configuration not found at {config_path}, using default"
                )
                model_config = RLLMModelConfig()
                model_config.model_id = model_path

            model = cls(
                model_config=model_config, device=device, logger=logger
            )

            model.load_model()

            return model

        except Exception as e:
            logger.error(f"Error loading model from pretrained: {e}")
            return None


class RLLMModelManager:
    """Manager for RLLM models."""

    def __init__(
        self,
        config: Optional[RLLMConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize manager.

        Args:
            config: Configuration
            logger: Logger
        """
        self.config = config or RLLMConfig()
        self.logger = logger or logging.getLogger("RLLMModelManager")

        self.models = {}

        self.logger.info("Initialized RLLM model manager")

    def load_model(
        self, model_id: Optional[str] = None, device: Optional[str] = None
    ) -> Optional[RLLMModel]:
        """
        Load model.

        Args:
            model_id: Model ID
            device: Device to use

        Returns:
            Model
        """
        model_id = model_id or self.config.model.model_id

        if model_id in self.models:
            self.logger.info(f"Model {model_id} already loaded")
            return self.models[model_id]

        try:
            self.logger.info(f"Loading model {model_id}")

            model_config = self.config.model
            if model_id != model_config.model_id:
                model_config = RLLMModelConfig()
                model_config.model_id = model_id

            model = RLLMModel(
                model_config=model_config, device=device, logger=self.logger
            )

            model.load_model()

            self.models[model_id] = model

            return model

        except Exception as e:
            self.logger.error(f"Error loading model {model_id}: {e}")
            return None

    def get_model(self, model_id: Optional[str] = None) -> Optional[RLLMModel]:
        """
        Get model.

        Args:
            model_id: Model ID

        Returns:
            Model
        """
        model_id = model_id or self.config.model.model_id

        if model_id in self.models:
            return self.models[model_id]

        return self.load_model(model_id)

    def unload_model(self, model_id: str) -> None:
        """
        Unload model.

        Args:
            model_id: Model ID
        """
        if model_id in self.models:
            self.logger.info(f"Unloading model {model_id}")

            del self.models[model_id]

            import gc

            gc.collect()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.logger.info(f"Model {model_id} unloaded")
