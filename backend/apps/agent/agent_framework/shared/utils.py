"""
Shared utility functions for agent framework.

This module provides shared utility functions that can be used by both Kled and Veigar agents.
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def find_repo_root(start_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Find the repository root from the given path.
    
    Args:
        start_path: Path to start searching from. If None, uses the current working directory.
        
    Returns:
        Path: Path to the repository root.
        
    Raises:
        ValueError: If the repository root cannot be found.
    """
    if start_path is None:
        start_path = os.getcwd()
    
    path = Path(start_path).resolve()
    
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    
    raise ValueError(f"Could not find repository root from {start_path}")


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Dict[str, Any]: The loaded JSON data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(file_path, "r") as f:
        return json.load(f)


def save_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
    """
    Save data to a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        data: Data to save.
        indent: Indentation level for the JSON file.
        
    Raises:
        IOError: If the file cannot be written.
    """
    with open(file_path, "w") as f:
        json.dump(data, f, indent=indent)


def load_text_file(file_path: Union[str, Path]) -> str:
    """
    Load a text file.
    
    Args:
        file_path: Path to the text file.
        
    Returns:
        str: The loaded text.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with open(file_path, "r") as f:
        return f.read()


def save_text_file(file_path: Union[str, Path], text: str) -> None:
    """
    Save text to a file.
    
    Args:
        file_path: Path to the text file.
        text: Text to save.
        
    Raises:
        IOError: If the file cannot be written.
    """
    with open(file_path, "w") as f:
        f.write(text)


def ensure_directory_exists(directory_path: Union[str, Path]) -> None:
    """
    Ensure that the given directory exists.
    
    Args:
        directory_path: Path to the directory.
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def get_module_path(module_name: str) -> Optional[Path]:
    """
    Get the path to a module.
    
    Args:
        module_name: Name of the module.
        
    Returns:
        Optional[Path]: Path to the module, or None if the module cannot be found.
    """
    try:
        module = __import__(module_name)
        return Path(module.__file__).parent
    except (ImportError, AttributeError):
        return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Filename to sanitize.
        
    Returns:
        str: Sanitized filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "_", filename)
