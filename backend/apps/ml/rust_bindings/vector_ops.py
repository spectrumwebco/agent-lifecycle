"""
Python interface to Rust implementation of vector operations.
"""
from typing import List, Tuple, Optional
import numpy as np

try:
    from agent_runtime_rust.ml_core import cosine_similarity, batch_cosine_similarity, knn_search
except ImportError:
    cosine_similarity = None
    batch_cosine_similarity = None
    knn_search = None


def compute_cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity value
    """
    if cosine_similarity is not None:
        return cosine_similarity(a, b)
    else:
        a_np = np.array(a)
        b_np = np.array(b)
        return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))


def compute_batch_cosine_similarity(query: List[float], matrix: List[List[float]]) -> List[float]:
    """
    Compute cosine similarity between a query vector and a matrix of vectors.
    
    Args:
        query: Query vector
        matrix: Matrix of vectors
        
    Returns:
        List of cosine similarity values
    """
    if batch_cosine_similarity is not None:
        return batch_cosine_similarity(query, matrix)
    else:
        query_np = np.array(query)
        matrix_np = np.array(matrix)
        
        dot_product = np.dot(matrix_np, query_np)
        
        query_norm = np.linalg.norm(query_np)
        matrix_norm = np.linalg.norm(matrix_np, axis=1)
        
        return (dot_product / (matrix_norm * query_norm)).tolist()


def compute_knn_search(query: List[float], matrix: List[List[float]], k: int) -> Tuple[List[int], List[float]]:
    """
    Perform k-nearest neighbors search.
    
    Args:
        query: Query vector
        matrix: Matrix of vectors
        k: Number of nearest neighbors to return
        
    Returns:
        Tuple of (indices, similarity values)
    """
    if knn_search is not None:
        return knn_search(query, matrix, k)
    else:
        similarities = compute_batch_cosine_similarity(query, matrix)
        
        indexed_sims = list(enumerate(similarities))
        
        indexed_sims.sort(key=lambda x: x[1], reverse=True)
        
        top_k = indexed_sims[:k]
        
        indices = [idx for idx, _ in top_k]
        values = [val for _, val in top_k]
        
        return indices, values
