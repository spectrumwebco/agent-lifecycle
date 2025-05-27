"""
File utility functions for Python agents.

This module provides file-related utility functions that can be used by both
Kled and Veigar agents.
"""

import os
import shutil
import tempfile
from typing import List, Optional, Tuple, Callable

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory.
    """
    os.makedirs(directory_path, exist_ok=True)

def list_files(directory_path: str, extension: Optional[str] = None) -> List[str]:
    """
    List all files in a directory, optionally filtered by extension.
    
    Args:
        directory_path: Path to the directory.
        extension: Optional file extension to filter by (e.g., '.py').
        
    Returns:
        A list of file paths.
    """
    if not os.path.exists(directory_path):
        return []
    
    files = []
    for root, _, filenames in os.walk(directory_path):
        for filename in filenames:
            if extension is None or filename.endswith(extension):
                files.append(os.path.join(root, filename))
    
    return files

def create_temp_directory() -> Tuple[str, Callable]:
    """
    Create a temporary directory.
    
    Returns:
        A tuple containing the path to the temporary directory and a function to clean it up.
    """
    temp_dir = tempfile.mkdtemp()
    
    def cleanup():
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    return temp_dir, cleanup

def copy_file(source_path: str, destination_path: str) -> None:
    """
    Copy a file from source to destination.
    
    Args:
        source_path: Path to the source file.
        destination_path: Path to the destination file.
        
    Raises:
        FileNotFoundError: If the source file does not exist.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    destination_dir = os.path.dirname(destination_path)
    ensure_directory_exists(destination_dir)
    
    shutil.copy2(source_path, destination_path)

def move_file(source_path: str, destination_path: str) -> None:
    """
    Move a file from source to destination.
    
    Args:
        source_path: Path to the source file.
        destination_path: Path to the destination file.
        
    Raises:
        FileNotFoundError: If the source file does not exist.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    destination_dir = os.path.dirname(destination_path)
    ensure_directory_exists(destination_dir)
    
    shutil.move(source_path, destination_path)

def read_file(file_path: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        The contents of the file as a string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return f.read()

def write_file(file_path: str, content: str) -> None:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file.
        content: Content to write to the file.
    """
    directory = os.path.dirname(file_path)
    ensure_directory_exists(directory)
    
    with open(file_path, 'w') as f:
        f.write(content)

def append_to_file(file_path: str, content: str) -> None:
    """
    Append content to a file.
    
    Args:
        file_path: Path to the file.
        content: Content to append to the file.
    """
    directory = os.path.dirname(file_path)
    ensure_directory_exists(directory)
    
    with open(file_path, 'a') as f:
        f.write(content)
