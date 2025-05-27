"""
Python interface to Rust implementations for performance-critical components.
"""
from .utils import get_trajectory_dataset
from .fast_tokenizer import get_fast_tokenizer, fast_tokenize, RUST_AVAILABLE
from .vector_ops import (
    compute_cosine_similarity,
    compute_batch_cosine_similarity,
    compute_knn_search,
)
from .pydantic_ext import create_rust_validator
