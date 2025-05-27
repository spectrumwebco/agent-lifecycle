"""
Python interface to Rust implementation of trajectory dataset processing.
"""
from typing import Dict, List, Optional, Union
import json
import os

try:
    from agent_runtime_rust.ml_core import RustTrajectoryDataset
except ImportError:
    RustTrajectoryDataset = None


class RLLMTrajectoryDatasetRust:
    """
    Python wrapper for the Rust implementation of RLLMTrajectoryDataset.
    Falls back to Python implementation if Rust bindings are not available.
    """
    
    def __init__(
        self,
        trajectories: List[Dict[str, Union[str, float]]],
        system_prompt: str,
        max_length: int = 2048
    ):
        """
        Initialize the trajectory dataset.
        
        Args:
            trajectories: List of trajectory dictionaries with input_text, output_text, and reward
            system_prompt: System prompt to use for the model
            max_length: Maximum sequence length
        """
        self.system_prompt = system_prompt
        self.max_length = max_length
        
        if RustTrajectoryDataset is not None:
            self._rust_dataset = RustTrajectoryDataset(trajectories, system_prompt, max_length)
            self.trajectories = self._rust_dataset.trajectories
        else:
            self.trajectories = trajectories
    
    @classmethod
    def from_jsonl(cls, path: str, system_prompt: str, max_length: int = 2048) -> "RLLMTrajectoryDatasetRust":
        """
        Load trajectories from a JSONL file.
        
        Args:
            path: Path to the JSONL file
            system_prompt: System prompt to use for the model
            max_length: Maximum sequence length
            
        Returns:
            RLLMTrajectoryDatasetRust instance
        """
        if RustTrajectoryDataset is not None:
            rust_dataset = RustTrajectoryDataset.from_jsonl(path, system_prompt, max_length)
            instance = cls.__new__(cls)
            instance._rust_dataset = rust_dataset
            instance.system_prompt = system_prompt
            instance.max_length = max_length
            instance.trajectories = rust_dataset.trajectories
            return instance
        else:
            trajectories = []
            with open(path, 'r') as f:
                for line in f:
                    if line.strip():
                        trajectories.append(json.loads(line))
            return cls(trajectories, system_prompt, max_length)
    
    def save_to_jsonl(self, path: str) -> None:
        """
        Save trajectories to a JSONL file.
        
        Args:
            path: Path to save the JSONL file
        """
        if RustTrajectoryDataset is not None:
            self._rust_dataset.save_to_jsonl(path)
        else:
            with open(path, 'w') as f:
                for traj in self.trajectories:
                    f.write(json.dumps(traj) + '\n')
    
    def to_dict(self) -> Dict:
        """
        Convert the dataset to a dictionary.
        
        Returns:
            Dictionary representation of the dataset
        """
        if RustTrajectoryDataset is not None:
            import inspect
            if 'py' in inspect.signature(self._rust_dataset.to_python_dict).parameters:
                import pyo3
                with pyo3.Python.acquire_gil() as gil:
                    return self._rust_dataset.to_python_dict(gil.python())
            else:
                return self._rust_dataset.to_python_dict()
        else:
            return {
                "trajectories": self.trajectories,
                "system_prompt": self.system_prompt,
                "max_length": self.max_length
            }
