"""
Python interface to Rust implementation of RLLM model.
"""
from typing import Dict, List, Optional, Union, Any
import json
import os

try:
    from agent_runtime_rust.ml_core import RustRLLMModel
except ImportError:
    RustRLLMModel = None


class RLLMModelRust:
    """
    Python wrapper for the Rust implementation of RLLMModel.
    Falls back to Python implementation if Rust bindings are not available.
    """
    
    def __init__(
        self,
        model_name: str,
        tokenizer_name: str,
        max_length: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        model: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
    ):
        """
        Initialize the RLLM model.
        
        Args:
            model_name: Name of the model
            tokenizer_name: Name of the tokenizer
            max_length: Maximum sequence length
            temperature: Temperature for sampling
            top_p: Top-p for sampling
            model: Optional model instance
            tokenizer: Optional tokenizer instance
        """
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p
        self._model = model
        self._tokenizer = tokenizer
        
        if RustRLLMModel is not None and model is not None and tokenizer is not None:
            self._rust_model = RustRLLMModel(
                model_name,
                tokenizer_name,
                max_length,
                temperature,
                top_p,
                model,
                tokenizer,
            )
        else:
            self._rust_model = None
    
    def batch_tokenize(self, texts: List[str]) -> List[Dict]:
        """
        Tokenize a batch of texts.
        
        Args:
            texts: List of texts to tokenize
            
        Returns:
            List of tokenized inputs
        """
        if self._rust_model is not None:
            import inspect
            if 'py' in inspect.signature(self._rust_model.batch_tokenize).parameters:
                import pyo3
                with pyo3.Python.acquire_gil() as gil:
                    return self._rust_model.batch_tokenize(gil.python(), texts)
            else:
                return self._rust_model.batch_tokenize(texts)
        else:
            if self._tokenizer is None:
                raise ValueError("Tokenizer not initialized")
            
            return [
                self._tokenizer(
                    text,
                    max_length=self.max_length,
                    padding="max_length",
                    truncation=True,
                    return_tensors="pt",
                )
                for text in texts
            ]
    
    def batch_generate(self, prompts: List[str]) -> List[str]:
        """
        Generate text from a batch of prompts.
        
        Args:
            prompts: List of prompts
            
        Returns:
            List of generated texts
        """
        if self._rust_model is not None:
            import inspect
            if 'py' in inspect.signature(self._rust_model.batch_generate).parameters:
                import pyo3
                with pyo3.Python.acquire_gil() as gil:
                    return self._rust_model.batch_generate(gil.python(), prompts)
            else:
                return self._rust_model.batch_generate(prompts)
        else:
            if self._model is None or self._tokenizer is None:
                raise ValueError("Model or tokenizer not initialized")
            
            tokenized = self.batch_tokenize(prompts)
            generated = self._model.generate(
                tokenized,
                max_length=self.max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True,
            )
            
            return self._tokenizer.batch_decode(generated)
    
    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """
        Calculate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        if self._rust_model is not None:
            import inspect
            if 'py' in inspect.signature(self._rust_model.batch_embed).parameters:
                import pyo3
                with pyo3.Python.acquire_gil() as gil:
                    return self._rust_model.batch_embed(gil.python(), texts)
            else:
                return self._rust_model.batch_embed(texts)
        else:
            if self._model is None:
                raise ValueError("Model not initialized")
            
            tokenized = self.batch_tokenize(texts)
            return self._model.encode(tokenized)
    
    def save_config(self, path: str) -> None:
        """
        Save the model configuration to a JSON file.
        
        Args:
            path: Path to save the configuration
        """
        if self._rust_model is not None:
            self._rust_model.save_config(path)
        else:
            config = {
                "model_name": self.model_name,
                "tokenizer_name": self.tokenizer_name,
                "max_length": self.max_length,
                "temperature": self.temperature,
                "top_p": self.top_p,
            }
            
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
    
    @classmethod
    def load_config(cls, path: str, model: Any, tokenizer: Any) -> "RLLMModelRust":
        """
        Load the model configuration from a JSON file.
        
        Args:
            path: Path to the configuration file
            model: Model instance
            tokenizer: Tokenizer instance
            
        Returns:
            RLLMModelRust instance
        """
        if RustRLLMModel is not None:
            import inspect
            if 'py' in inspect.signature(RustRLLMModel.load_config).parameters:
                import pyo3
                with pyo3.Python.acquire_gil() as gil:
                    rust_model = RustRLLMModel.load_config(gil.python(), path, model, tokenizer)
            else:
                rust_model = RustRLLMModel.load_config(path, model, tokenizer)
            
            instance = cls.__new__(cls)
            instance._rust_model = rust_model
            instance.model_name = rust_model.model_name
            instance.tokenizer_name = rust_model.tokenizer_name
            instance.max_length = rust_model.max_length
            instance.temperature = rust_model.temperature
            instance.top_p = rust_model.top_p
            instance._model = model
            instance._tokenizer = tokenizer
            return instance
        else:
            with open(path, 'r') as f:
                config = json.load(f)
            
            return cls(
                model_name=config["model_name"],
                tokenizer_name=config["tokenizer_name"],
                max_length=config["max_length"],
                temperature=config["temperature"],
                top_p=config["top_p"],
                model=model,
                tokenizer=tokenizer,
            )
