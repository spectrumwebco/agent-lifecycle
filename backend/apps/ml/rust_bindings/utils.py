"""
Utility functions for Rust bindings.
"""
from typing import Optional, Any, Type

def get_trajectory_dataset() -> Optional[Type]:
    """
    Get the Rust implementation of the trajectory dataset if available.
    
    Returns:
        RustTrajectoryDataset class if available, None otherwise
    """
    try:
        from agent_runtime_rust.ml_core import RustTrajectoryDataset
        return RustTrajectoryDataset
    except ImportError:
        return None
