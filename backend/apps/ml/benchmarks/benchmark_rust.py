"""
Benchmark Rust implementations against Python ones.
"""

import time
import argparse
import numpy as np
import json
import logging
from pathlib import Path
import os
import sys

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from ..rust_bindings import (
    get_trajectory_dataset,
    get_fast_tokenizer,
    compute_cosine_similarity,
    compute_batch_cosine_similarity,
    compute_knn_search,
    RUST_AVAILABLE,
)
from ..data.trajectory_dataset import RLLMTrajectoryDataset as PyTrajectoryDataset
from ..models.rllm_model import RLLMModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("benchmark")


def benchmark_trajectory_dataset(data_path, iterations=5):
    """Benchmark trajectory dataset loading and processing."""
    rust_dataset_cls = get_trajectory_dataset()
    
    logger.info(f"Benchmarking trajectory dataset loading from {data_path}")
    
    if RUST_AVAILABLE and os.path.exists(data_path):
        py_times = []
        for i in range(iterations):
            logger.info(f"Python implementation - iteration {i+1}/{iterations}")
            start = time.time()
            py_dataset = PyTrajectoryDataset.from_jsonl(
                path=data_path,
                system_prompt="Test prompt",
                max_length=1024,
            )
            py_times.append(time.time() - start)
        
        rust_times = []
        for i in range(iterations):
            logger.info(f"Rust implementation - iteration {i+1}/{iterations}")
            start = time.time()
            rust_dataset = rust_dataset_cls.from_jsonl(
                data_path,
                "Test prompt",
                1024,
            )
            rust_times.append(time.time() - start)
        
        logger.info(f"TrajectoryDataset loading (Python): {np.mean(py_times):.4f}s ± {np.std(py_times):.4f}s")
        logger.info(f"TrajectoryDataset loading (Rust): {np.mean(rust_times):.4f}s ± {np.std(rust_times):.4f}s")
        logger.info(f"Speedup: {np.mean(py_times) / np.mean(rust_times):.2f}x")
    else:
        if not RUST_AVAILABLE:
            logger.info("Rust not available, skipping benchmark")
        else:
            logger.info(f"Data path {data_path} does not exist, skipping benchmark")


def benchmark_vector_ops(vector_dim=768, num_vectors=10000, iterations=5):
    """Benchmark vector operations."""
    logger.info(f"Benchmarking vector operations with {num_vectors} vectors of dimension {vector_dim}")
    
    query = np.random.randn(vector_dim).astype(np.float32)
    matrix = np.random.randn(num_vectors, vector_dim).astype(np.float32)
    
    query_list = query.tolist()
    matrix_list = matrix.tolist()
    
    py_times = []
    for i in range(iterations):
        logger.info(f"Python implementation - iteration {i+1}/{iterations}")
        start = time.time()
        dots = np.dot(matrix, query)
        norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)
        similarities = dots / norms
        indices = np.argsort(similarities)[-10:][::-1]
        py_times.append(time.time() - start)
    
    if RUST_AVAILABLE:
        rust_times = []
        for i in range(iterations):
            logger.info(f"Rust implementation - iteration {i+1}/{iterations}")
            start = time.time()
            indices, values = compute_knn_search(query_list, matrix_list, 10)
            rust_times.append(time.time() - start)
        
        logger.info(f"KNN search (Python): {np.mean(py_times):.4f}s ± {np.std(py_times):.4f}s")
        logger.info(f"KNN search (Rust): {np.mean(rust_times):.4f}s ± {np.std(rust_times):.4f}s")
        logger.info(f"Speedup: {np.mean(py_times) / np.mean(rust_times):.2f}x")
    else:
        logger.info("Rust not available, skipping benchmark")


def benchmark_cosine_similarity(vector_dim=768, iterations=5):
    """Benchmark cosine similarity calculation."""
    logger.info(f"Benchmarking cosine similarity with vectors of dimension {vector_dim}")
    
    a = np.random.randn(vector_dim).astype(np.float32)
    b = np.random.randn(vector_dim).astype(np.float32)
    
    a_list = a.tolist()
    b_list = b.tolist()
    
    py_times = []
    for i in range(iterations):
        logger.info(f"Python implementation - iteration {i+1}/{iterations}")
        start = time.time()
        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        py_times.append(time.time() - start)
    
    if RUST_AVAILABLE:
        rust_times = []
        for i in range(iterations):
            logger.info(f"Rust implementation - iteration {i+1}/{iterations}")
            start = time.time()
            similarity = compute_cosine_similarity(a_list, b_list)
            rust_times.append(time.time() - start)
        
        logger.info(f"Cosine similarity (Python): {np.mean(py_times):.4f}s ± {np.std(py_times):.4f}s")
        logger.info(f"Cosine similarity (Rust): {np.mean(rust_times):.4f}s ± {np.std(rust_times):.4f}s")
        logger.info(f"Speedup: {np.mean(py_times) / np.mean(rust_times):.2f}x")
    else:
        logger.info("Rust not available, skipping benchmark")


def benchmark_batch_cosine_similarity(vector_dim=768, num_vectors=1000, iterations=5):
    """Benchmark batch cosine similarity calculation."""
    logger.info(f"Benchmarking batch cosine similarity with {num_vectors} vectors of dimension {vector_dim}")
    
    query = np.random.randn(vector_dim).astype(np.float32)
    matrix = np.random.randn(num_vectors, vector_dim).astype(np.float32)
    
    query_list = query.tolist()
    matrix_list = matrix.tolist()
    
    py_times = []
    for i in range(iterations):
        logger.info(f"Python implementation - iteration {i+1}/{iterations}")
        start = time.time()
        dots = np.dot(matrix, query)
        norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)
        similarities = dots / norms
        py_times.append(time.time() - start)
    
    if RUST_AVAILABLE:
        rust_times = []
        for i in range(iterations):
            logger.info(f"Rust implementation - iteration {i+1}/{iterations}")
            start = time.time()
            similarities = compute_batch_cosine_similarity(query_list, matrix_list)
            rust_times.append(time.time() - start)
        
        logger.info(f"Batch cosine similarity (Python): {np.mean(py_times):.4f}s ± {np.std(py_times):.4f}s")
        logger.info(f"Batch cosine similarity (Rust): {np.mean(rust_times):.4f}s ± {np.std(rust_times):.4f}s")
        logger.info(f"Speedup: {np.mean(py_times) / np.mean(rust_times):.2f}x")
    else:
        logger.info("Rust not available, skipping benchmark")


def benchmark_tokenization(model_path=None, num_texts=100, iterations=5):
    """Benchmark tokenization."""
    if not TORCH_AVAILABLE:
        logger.info("PyTorch not available, skipping tokenization benchmark")
        return
    
    fast_tokenize = get_fast_tokenizer()
    
    if model_path is None:
        logger.info("No model path provided, skipping tokenization benchmark")
        return
    
    logger.info(f"Benchmarking tokenization with model at {model_path}")
    
    try:
        model = RLLMModel.from_pretrained(model_path)
        tokenizer = model.tokenizer
        
        if tokenizer is None:
            logger.info("Failed to load tokenizer, skipping tokenization benchmark")
            return
        
        texts = [
            "This is a sample text for tokenization benchmark.",
            "Another example text that will be tokenized.",
            "Machine learning models require efficient tokenization for good performance.",
            "Rust implementations can significantly speed up tokenization operations.",
            "Benchmarking helps quantify the performance improvements from Rust.",
        ] * (num_texts // 5 + 1)  # Multiply to get the desired batch size
        texts = texts[:num_texts]  # Trim to exact size
        
        logger.info(f"Benchmarking tokenization with {len(texts)} texts")
        
        py_times = []
        for i in range(iterations):
            logger.info(f"Python implementation - iteration {i+1}/{iterations}")
            start = time.time()
            tokens = tokenizer(
                texts,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512,
            )
            py_times.append(time.time() - start)
        
        if RUST_AVAILABLE and fast_tokenize is not None:
            rust_times = []
            for i in range(iterations):
                logger.info(f"Rust implementation - iteration {i+1}/{iterations}")
                start = time.time()
                tokens = fast_tokenize(
                    tokenizer,
                    texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt",
                )
                rust_times.append(time.time() - start)
            
            logger.info(f"Tokenization (Python): {np.mean(py_times):.4f}s ± {np.std(py_times):.4f}s")
            logger.info(f"Tokenization (Rust): {np.mean(rust_times):.4f}s ± {np.std(rust_times):.4f}s")
            logger.info(f"Speedup: {np.mean(py_times) / np.mean(rust_times):.2f}x")
        else:
            if not RUST_AVAILABLE:
                logger.info("Rust not available, skipping benchmark")
            else:
                logger.info("Fast tokenizer not available, skipping benchmark")
    
    except Exception as e:
        logger.error(f"Error in tokenization benchmark: {e}")


def save_benchmark_results(results, output_path):
    """Save benchmark results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Benchmark results saved to {output_path}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Benchmark Rust implementations")
    parser.add_argument("--data-path", type=str, help="Path to trajectory data")
    parser.add_argument("--model-path", type=str, help="Path to model")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Output file for results")
    parser.add_argument("--vector-dim", type=int, default=768, help="Vector dimension for vector operations")
    parser.add_argument("--num-vectors", type=int, default=10000, help="Number of vectors for batch operations")
    parser.add_argument("--num-texts", type=int, default=100, help="Number of texts for tokenization benchmark")
    parser.add_argument("--skip-trajectory", action="store_true", help="Skip trajectory dataset benchmark")
    parser.add_argument("--skip-vector-ops", action="store_true", help="Skip vector operations benchmark")
    parser.add_argument("--skip-tokenization", action="store_true", help="Skip tokenization benchmark")
    
    args = parser.parse_args()
    
    results = {
        "rust_available": RUST_AVAILABLE,
        "torch_available": TORCH_AVAILABLE,
        "timestamp": time.time(),
        "iterations": args.iterations,
    }
    
    if not args.skip_trajectory and args.data_path:
        logger.info("=== Trajectory Dataset Benchmark ===")
        benchmark_trajectory_dataset(args.data_path, args.iterations)
    
    if not args.skip_vector_ops:
        logger.info("=== Vector Operations Benchmark ===")
        logger.info("--- Cosine Similarity ---")
        benchmark_cosine_similarity(args.vector_dim, args.iterations)
        
        logger.info("--- Batch Cosine Similarity ---")
        benchmark_batch_cosine_similarity(args.vector_dim, args.num_vectors, args.iterations)
        
        logger.info("--- KNN Search ---")
        benchmark_vector_ops(args.vector_dim, args.num_vectors, args.iterations)
    
    if not args.skip_tokenization:
        logger.info("=== Tokenization Benchmark ===")
        benchmark_tokenization(args.model_path, args.num_texts, args.iterations)
    
    if args.output:
        save_benchmark_results(results, args.output)


if __name__ == "__main__":
    main()
