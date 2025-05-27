"""
Git utility functions for Python agents.

This module provides Git-related utility functions that can be used by both
Kled and Veigar agents.
"""

import os
import subprocess
from typing import List, Optional, Tuple

def run_git_command(command: List[str], cwd: Optional[str] = None) -> Tuple[str, str, int]:
    """
    Run a Git command.
    
    Args:
        command: Git command to run, as a list of strings.
        cwd: Working directory to run the command in.
        
    Returns:
        A tuple containing the stdout, stderr, and return code.
    """
    full_command = ['git'] + command
    
    process = subprocess.Popen(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    return stdout.strip(), stderr.strip(), process.returncode

def is_git_repository(directory: str) -> bool:
    """
    Check if a directory is a Git repository.
    
    Args:
        directory: Directory to check.
        
    Returns:
        True if the directory is a Git repository, False otherwise.
    """
    _, _, return_code = run_git_command(['rev-parse', '--is-inside-work-tree'], cwd=directory)
    return return_code == 0

def get_current_branch(directory: str) -> Optional[str]:
    """
    Get the current Git branch.
    
    Args:
        directory: Git repository directory.
        
    Returns:
        The current branch name, or None if not in a Git repository.
    """
    if not is_git_repository(directory):
        return None
    
    stdout, _, return_code = run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=directory)
    if return_code != 0:
        return None
    
    return stdout

def get_changed_files(directory: str, staged_only: bool = False) -> List[str]:
    """
    Get a list of changed files in a Git repository.
    
    Args:
        directory: Git repository directory.
        staged_only: If True, only return staged files.
        
    Returns:
        A list of changed file paths.
    """
    if not is_git_repository(directory):
        return []
    
    if staged_only:
        stdout, _, return_code = run_git_command(['diff', '--name-only', '--staged'], cwd=directory)
    else:
        stdout, _, return_code = run_git_command(['status', '--porcelain'], cwd=directory)
    
    if return_code != 0:
        return []
    
    if staged_only:
        return stdout.splitlines()
    else:
        files = []
        for line in stdout.splitlines():
            if line.strip():
                status = line[:2]
                file_path = line[3:].strip()
                files.append(file_path)
        return files

def clone_repository(url: str, target_directory: str, branch: Optional[str] = None) -> bool:
    """
    Clone a Git repository.
    
    Args:
        url: Repository URL.
        target_directory: Directory to clone into.
        branch: Branch to clone.
        
    Returns:
        True if the clone was successful, False otherwise.
    """
    command = ['clone', url, target_directory]
    if branch:
        command.extend(['--branch', branch])
    
    _, _, return_code = run_git_command(command)
    return return_code == 0

def checkout_branch(directory: str, branch: str, create: bool = False) -> bool:
    """
    Checkout a Git branch.
    
    Args:
        directory: Git repository directory.
        branch: Branch to checkout.
        create: If True, create the branch if it doesn't exist.
        
    Returns:
        True if the checkout was successful, False otherwise.
    """
    if not is_git_repository(directory):
        return False
    
    command = ['checkout']
    if create:
        command.append('-b')
    command.append(branch)
    
    _, _, return_code = run_git_command(command, cwd=directory)
    return return_code == 0

def commit_changes(directory: str, message: str, files: Optional[List[str]] = None) -> bool:
    """
    Commit changes to a Git repository.
    
    Args:
        directory: Git repository directory.
        message: Commit message.
        files: List of files to commit. If None, all staged files will be committed.
        
    Returns:
        True if the commit was successful, False otherwise.
    """
    if not is_git_repository(directory):
        return False
    
    if files:
        for file in files:
            _, _, return_code = run_git_command(['add', file], cwd=directory)
            if return_code != 0:
                return False
    
    _, _, return_code = run_git_command(['commit', '-m', message], cwd=directory)
    return return_code == 0

def push_changes(directory: str, remote: str = 'origin', branch: Optional[str] = None) -> bool:
    """
    Push changes to a remote Git repository.
    
    Args:
        directory: Git repository directory.
        remote: Remote name.
        branch: Branch to push. If None, the current branch will be pushed.
        
    Returns:
        True if the push was successful, False otherwise.
    """
    if not is_git_repository(directory):
        return False
    
    command = ['push', remote]
    if branch:
        command.append(branch)
    
    _, _, return_code = run_git_command(command, cwd=directory)
    return return_code == 0
