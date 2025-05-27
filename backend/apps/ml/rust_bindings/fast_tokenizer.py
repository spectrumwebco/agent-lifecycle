"""
Python interface to Rust implementation of fast tokenization.
"""
from typing import Dict, List, Optional, Union, Any
import torch

try:
    from agent_runtime_rust.ml_core import fast_tokenize as rust_fast_tokenize
    RUST_AVAILABLE = True
except ImportError:
    rust_fast_tokenize = None
    RUST_AVAILABLE = False


def get_fast_tokenizer():
    """
    Get the Rust implementation of fast tokenization if available.
    
    Returns:
        fast_tokenize function if available, None otherwise
    """
    if RUST_AVAILABLE:
        return fast_tokenize
    return None


def fast_tokenize(
    tokenizer: Any,
    text: Union[str, List[str]],
    padding: bool = True,
    truncation: bool = True,
    max_length: int = 512,
    return_tensors: str = "pt",
) -> Dict:
    """
    Fast tokenization using Rust implementation.
    
    Args:
        tokenizer: Hugging Face tokenizer
        text: Text or list of texts to tokenize
        padding: Whether to pad sequences
        truncation: Whether to truncate sequences
        max_length: Maximum sequence length
        return_tensors: Return format ('pt' for PyTorch, 'np' for NumPy)
        
    Returns:
        Tokenized inputs
    """
    if rust_fast_tokenize is not None:
        try:
            if isinstance(text, str):
                text = [text]
                
            result = rust_fast_tokenize(
                tokenizer,
                text,
                padding,
                truncation,
                max_length,
            )
            
            if return_tensors == "pt":
                for key, value in result.items():
                    if isinstance(value, list):
                        result[key] = torch.tensor(value)
            
            return result
        except Exception as e:
            import logging
            logging.getLogger("fast_tokenizer").warning(
                f"Error in Rust tokenization, falling back to Python: {e}"
            )
    
    return tokenizer(
        text,
        padding=padding,
        truncation=truncation,
        max_length=max_length,
        return_tensors=return_tensors,
    )
