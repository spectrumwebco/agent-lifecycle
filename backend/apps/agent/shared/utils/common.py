"""
Common utility functions for Python agents.

This module provides common utility functions that can be used by both
Kled and Veigar agents.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        The contents of the JSON file as a dictionary.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """
    Save a dictionary as a JSON file.
    
    Args:
        file_path: Path to save the JSON file.
        data: Dictionary to save.
        indent: Number of spaces to use for indentation.
        
    Raises:
        TypeError: If the data is not JSON serializable.
    """
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries recursively.
    
    Args:
        dict1: First dictionary.
        dict2: Second dictionary.
        
    Returns:
        A new dictionary containing the merged contents of both dictionaries.
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def get_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Get an environment variable.
    
    Args:
        name: Name of the environment variable.
        default: Default value to return if the environment variable is not set.
        
    Returns:
        The value of the environment variable, or the default value if not set.
        
    Raises:
        ValueError: If the environment variable is not set and no default is provided.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} is not set and no default value was provided.")
    
    return value

def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level.
        log_file: Path to the log file. If None, logs will be output to the console only.
    """
    log_level = getattr(logging, level.upper())
    
    handlers = []
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    handlers.append(logging.StreamHandler())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
