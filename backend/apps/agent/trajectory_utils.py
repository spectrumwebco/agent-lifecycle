"""
Utility functions for working with trajectories in the root directory.

This module provides functions for reading, writing, and managing trajectories
in the root trajectories directory, which is shared between the ML App and
the AI Agent components.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.utils import timezone

from apps.agent.kled.agent.types import Trajectory, TrajectoryStep


class TrajectoryManager:
    """
    Manager class for handling trajectories in the root directory.
    
    This class provides methods for reading, writing, and managing trajectories
    in the root trajectories directory, which is shared between the ML App and
    the AI Agent components.
    """
    
    def __init__(self):
        """Initialize the trajectory manager."""
        try:
            from apps.agent.kled.agent import REPO_ROOT
            self.root_dir = REPO_ROOT
        except ImportError:
            self.root_dir = Path(settings.BASE_DIR).parent.parent
        
        self.trajectories_dir = self.root_dir / 'trajectories'
        os.makedirs(self.trajectories_dir, exist_ok=True)
    
    def get_trajectory_path(self, trajectory_id: str) -> Path:
        """
        Get the path to a trajectory file.
        
        Args:
            trajectory_id: The ID of the trajectory.
            
        Returns:
            Path to the trajectory file.
        """
        return self.trajectories_dir / f"{trajectory_id}.json"
    
    def save_trajectory(self, trajectory: Trajectory, trajectory_id: Optional[str] = None) -> str:
        """
        Save a trajectory to the trajectories directory.
        
        Args:
            trajectory: The trajectory to save.
            trajectory_id: Optional ID for the trajectory. If not provided, a timestamp-based ID will be generated.
            
        Returns:
            The ID of the saved trajectory.
        """
        if trajectory_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            trajectory_id = f"trajectory_{timestamp}"
        
        trajectory_path = self.get_trajectory_path(trajectory_id)
        
        trajectory_data = []
        for step in trajectory:
            serializable_step = {}
            for key, value in step.items():
                if isinstance(value, dict):
                    serializable_step[key] = {
                        k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v
                        for k, v in value.items()
                    }
                elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    serializable_step[key] = str(value)
                else:
                    serializable_step[key] = value
            trajectory_data.append(serializable_step)
        
        with open(trajectory_path, 'w') as f:
            json.dump(trajectory_data, f, indent=2)
        
        return trajectory_id
    
    def load_trajectory(self, trajectory_id: str) -> Optional[Trajectory]:
        """
        Load a trajectory from the trajectories directory.
        
        Args:
            trajectory_id: The ID of the trajectory to load.
            
        Returns:
            The loaded trajectory, or None if the trajectory does not exist.
        """
        trajectory_path = self.get_trajectory_path(trajectory_id)
        
        if not trajectory_path.exists():
            return None
        
        with open(trajectory_path, 'r') as f:
            trajectory_data = json.load(f)
        
        trajectory: Trajectory = []
        for step_data in trajectory_data:
            trajectory.append(TrajectoryStep(**step_data))
        
        return trajectory
    
    def list_trajectories(self) -> List[str]:
        """
        List all trajectories in the trajectories directory.
        
        Returns:
            A list of trajectory IDs.
        """
        trajectory_files = self.trajectories_dir.glob("*.json")
        return [path.stem for path in trajectory_files]
    
    def delete_trajectory(self, trajectory_id: str) -> bool:
        """
        Delete a trajectory from the trajectories directory.
        
        Args:
            trajectory_id: The ID of the trajectory to delete.
            
        Returns:
            True if the trajectory was deleted, False otherwise.
        """
        trajectory_path = self.get_trajectory_path(trajectory_id)
        
        if not trajectory_path.exists():
            return False
        
        os.remove(trajectory_path)
        return True


trajectory_manager = TrajectoryManager()
