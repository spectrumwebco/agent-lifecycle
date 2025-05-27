"""
Neovim state integration for the shared state system.

This module provides integration between Neovim and the shared state system,
allowing Neovim state to be persisted and synchronized across components.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integrations.shared_state import SharedState

logger = logging.getLogger(__name__)

class NeovimStateEntry(BaseModel):
    """Neovim state entry for a specific instance."""
    instance_id: str = Field(..., description="Unique identifier for the Neovim instance")
    buffers: List[Dict[str, Any]] = Field(default_factory=list, description="List of open buffers")
    cursor_positions: Dict[str, Dict[str, int]] = Field(default_factory=dict, 
                                                       description="Cursor positions for each buffer")
    registers: Dict[str, str] = Field(default_factory=dict, description="Neovim registers")
    marks: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Neovim marks")
    options: Dict[str, Any] = Field(default_factory=dict, description="Neovim options")
    last_updated: int = Field(..., description="Timestamp of last update")
    active: bool = Field(default=True, description="Whether the instance is active")

class NeovimStateManager:
    """Manager for Neovim state in the shared state system."""
    def __init__(self, shared_state: Optional[SharedState] = None):
        """Initialize the Neovim state manager.
        
        Args:
            shared_state: Optional shared state instance to use
        """
        self.shared_state = shared_state or SharedState()
        self._neovim_instances = {}
        self._neovim_lock = threading.RLock()
        self._sync_threads = {}
        self._running = False
        
        self.shared_state.register_handler(self._handle_state_update)
    
    def _handle_state_update(self, state: Dict[str, Any]):
        """Handle a state update from the shared state system.
        
        Args:
            state: The updated state
        """
        if 'neovim' not in state:
            return
        
        neovim_state = state.get('neovim', {})
        
        with self._neovim_lock:
            for instance_id, instance_state in neovim_state.items():
                if instance_id in self._neovim_instances:
                    self._neovim_instances[instance_id].update(instance_state)
                else:
                    self._neovim_instances[instance_id] = instance_state
    
    def start(self) -> bool:
        """Start the Neovim state manager.
        
        Returns:
            bool: True if started successfully
        """
        if self._running:
            logger.warning("Neovim state manager already running")
            return True
        
        self._running = True
        
        if not getattr(self.shared_state, '_running', False):
            self.shared_state.start()
        
        logger.info("Started Neovim state manager")
        return True
    
    def stop(self) -> bool:
        """Stop the Neovim state manager.
        
        Returns:
            bool: True if stopped successfully
        """
        if not self._running:
            logger.warning("Neovim state manager not running")
            return True
        
        self._running = False
        
        for instance_id in list(self._sync_threads.keys()):
            self.stop_sync(instance_id)
        
        logger.info("Stopped Neovim state manager")
        return True
    
    def get_instance_state(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get the state for a specific Neovim instance.
        
        Args:
            instance_id: Unique identifier for the Neovim instance
        
        Returns:
            Optional[Dict[str, Any]]: The instance state, or None if not found
        """
        with self._neovim_lock:
            return self._neovim_instances.get(instance_id)
    
    def update_instance_state(self, instance_id: str, state_update: Dict[str, Any]) -> bool:
        """Update the state for a specific Neovim instance.
        
        Args:
            instance_id: Unique identifier for the Neovim instance
            state_update: The state update
        
        Returns:
            bool: True if updated successfully
        """
        with self._neovim_lock:
            if instance_id in self._neovim_instances:
                self._neovim_instances[instance_id].update(state_update)
            else:
                self._neovim_instances[instance_id] = state_update
            
            return self.shared_state.update_state({
                'neovim': {
                    instance_id: self._neovim_instances[instance_id]
                }
            })
    
    def start_sync(self, instance_id: str, neovim_api_base: str, interval: float = 5.0) -> bool:
        """Start syncing a Neovim instance with the shared state.
        
        Args:
            instance_id: Unique identifier for the Neovim instance
            neovim_api_base: Base URL for the Neovim API
            interval: Sync interval in seconds
        
        Returns:
            bool: True if sync started successfully
        """
        if instance_id in self._sync_threads:
            logger.warning("Sync already running for Neovim instance: %s", instance_id)
            return True
        
        thread = threading.Thread(
            target=self._sync_loop,
            args=(instance_id, neovim_api_base, interval)
        )
        thread.daemon = True
        thread.start()
        
        self._sync_threads[instance_id] = thread
        
        logger.info("Started sync for Neovim instance: %s", instance_id)
        return True
    
    def stop_sync(self, instance_id: str) -> bool:
        """Stop syncing a Neovim instance with the shared state.
        
        Args:
            instance_id: Unique identifier for the Neovim instance
        
        Returns:
            bool: True if sync stopped successfully
        """
        if instance_id not in self._sync_threads:
            logger.warning("No sync running for Neovim instance: %s", instance_id)
            return True
        
        self.update_instance_state(instance_id, {'active': False})
        self._sync_threads.pop(instance_id)
        
        logger.info("Stopped sync for Neovim instance: %s", instance_id)
        return True
    
    def _sync_loop(self, instance_id: str, neovim_api_base: str, interval: float):
        """Sync loop for a Neovim instance.
        
        Args:
            instance_id: Unique identifier for the Neovim instance
            neovim_api_base: Base URL for the Neovim API
            interval: Sync interval in seconds
        """
        import requests
        
        while self._running and instance_id in self._sync_threads:
            try:
                response = requests.get(
                    f"{neovim_api_base}/state",
                    params={"id": instance_id},
                    timeout=10
                )
                
                if response.status_code == 200:
                    neovim_state = response.json()
                    
                    state_update = {
                        'buffers': neovim_state.get('buffers', []),
                        'cursor_positions': neovim_state.get('cursor_positions', {}),
                        'registers': neovim_state.get('registers', {}),
                        'marks': neovim_state.get('marks', {}),
                        'options': neovim_state.get('options', {}),
                        'last_updated': int(time.time()),
                        'active': True
                    }
                    
                    self.update_instance_state(instance_id, state_update)
                else:
                    logger.warning("Failed to get Neovim state: %s", response.text)
            except Exception as e:
                logger.error("Error in sync loop: %s", e)
            
            time.sleep(interval)
    
    def restore_instance_state(self, instance_id: str, neovim_api_base: str) -> bool:
        """Restore a Neovim instance state from the shared state.
        
        Args:
            instance_id: Unique identifier for the Neovim instance
            neovim_api_base: Base URL for the Neovim API
        
        Returns:
            bool: True if restored successfully
        """
        import requests
        
        try:
            instance_state = self.get_instance_state(instance_id)
            
            if not instance_state:
                logger.warning("No state found for Neovim instance: %s", instance_id)
                return False
            
            neovim_state = {
                'buffers': instance_state.get('buffers', []),
                'cursor_positions': instance_state.get('cursor_positions', {}),
                'registers': instance_state.get('registers', {}),
                'marks': instance_state.get('marks', {}),
                'options': instance_state.get('options', {})
            }
            
            response = requests.post(
                f"{neovim_api_base}/restore",
                json={"id": instance_id, "state": neovim_state},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Restored state for Neovim instance: %s", instance_id)
                return True
            
            logger.error("Failed to restore Neovim state: %s", response.text)
            return False
        except Exception as e:
            logger.error("Error restoring Neovim state: %s", e)
            return False
    
    def list_instances(self, active_only: bool = False) -> List[str]:
        """List all Neovim instances in the shared state.
        
        Args:
            active_only: Whether to only include active instances
        
        Returns:
            List[str]: List of instance IDs
        """
        with self._neovim_lock:
            if active_only:
                return [
                    instance_id for instance_id, state in self._neovim_instances.items()
                    if state.get('active', False)
                ]
            return list(self._neovim_instances.keys())
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

neovim_state_manager = NeovimStateManager()
