"""
Real-time database integration for Neovim.

This module provides integration with Supabase for real-time state persistence
of Neovim sessions.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import asyncio
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class NeovimStateModel(BaseModel):
    """Neovim state model for database storage."""
    
    instance_id: str = Field(..., description="Unique identifier for the Neovim instance")
    buffers: List[Dict[str, Any]] = Field(default_factory=list, description="List of open buffers")
    cursor_positions: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Cursor positions for each buffer")
    registers: Dict[str, str] = Field(default_factory=dict, description="Neovim registers")
    marks: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Neovim marks")
    options: Dict[str, Any] = Field(default_factory=dict, description="Neovim options")
    last_updated: int = Field(..., description="Timestamp of last update")
    active: bool = Field(default=True, description="Whether the instance is active")

class SupabaseClient:
    """Client for interacting with Supabase."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """Initialize the Supabase client."""
        self.url = url or os.environ.get("SUPABASE_URL", "http://supabase-http.supabase.svc.cluster.local:8000")
        self.key = key or os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZW50LXJ1bnRpbWUiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjQxMjgwMCwiZXhwIjoxOTMyMDAwMDAwfQ.example")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}"
        }
        self._create_tables_if_not_exist()
    
    def _create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist."""
        try:
            response = requests.get(
                f"{self.url}/rest/v1/neovim_states?limit=1",
                headers=self.headers
            )
            
            if response.status_code == 404:
                sql = """
                CREATE TABLE IF NOT EXISTS neovim_states (
                    instance_id TEXT PRIMARY KEY,
                    buffers JSONB,
                    cursor_positions JSONB,
                    registers JSONB,
                    marks JSONB,
                    options JSONB,
                    last_updated BIGINT,
                    active BOOLEAN
                );
                """
                
                response = requests.post(
                    f"{self.url}/rest/v1/rpc/execute_sql",
                    headers=self.headers,
                    json={"query": sql}
                )
                
                if response.status_code == 200:
                    logger.info("Created neovim_states table")
                else:
                    logger.error(f"Failed to create neovim_states table: {response.text}")
        
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
    
    def save_state(self, state: NeovimStateModel) -> bool:
        """Save a Neovim state to the database."""
        try:
            data = state.dict()
            
            response = requests.post(
                f"{self.url}/rest/v1/neovim_states",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 409:
                response = requests.patch(
                    f"{self.url}/rest/v1/neovim_states?instance_id=eq.{state.instance_id}",
                    headers=self.headers,
                    json=data
                )
            
            return response.status_code in (200, 201, 204)
        
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            return False
    
    def load_state(self, instance_id: str) -> Optional[NeovimStateModel]:
        """Load a Neovim state from the database."""
        try:
            response = requests.get(
                f"{self.url}/rest/v1/neovim_states?instance_id=eq.{instance_id}",
                headers=self.headers
            )
            
            if response.status_code == 200 and response.json():
                data = response.json()[0]
                return NeovimStateModel(**data)
            
            return None
        
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return None
    
    def delete_state(self, instance_id: str) -> bool:
        """Delete a Neovim state from the database."""
        try:
            response = requests.delete(
                f"{self.url}/rest/v1/neovim_states?instance_id=eq.{instance_id}",
                headers=self.headers
            )
            
            return response.status_code == 204
        
        except Exception as e:
            logger.error(f"Error deleting state: {e}")
            return False
    
    def list_states(self, active_only: bool = False) -> List[NeovimStateModel]:
        """List all Neovim states in the database."""
        try:
            url = f"{self.url}/rest/v1/neovim_states"
            if active_only:
                url += "?active=eq.true"
            
            response = requests.get(
                url,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return [NeovimStateModel(**data) for data in response.json()]
            
            return []
        
        except Exception as e:
            logger.error(f"Error listing states: {e}")
            return []

class NeovimDatabaseIntegration:
    """Integration between Neovim and the real-time database."""
    
    def __init__(self):
        """Initialize the Neovim database integration."""
        self.db_client = SupabaseClient()
        self.sync_interval = 5.0  # seconds
        self._sync_tasks = {}
    
    async def start_sync(self, instance_id: str, neovim_api_base: str) -> bool:
        """Start syncing a Neovim instance with the database."""
        if instance_id in self._sync_tasks:
            return True
        
        task = asyncio.create_task(self._sync_loop(instance_id, neovim_api_base))
        self._sync_tasks[instance_id] = task
        
        logger.info(f"Started database sync for Neovim instance: {instance_id}")
        return True
    
    async def stop_sync(self, instance_id: str) -> bool:
        """Stop syncing a Neovim instance with the database."""
        if instance_id not in self._sync_tasks:
            return True
        
        task = self._sync_tasks[instance_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        del self._sync_tasks[instance_id]
        
        state = self.db_client.load_state(instance_id)
        if state:
            state.active = False
            self.db_client.save_state(state)
        
        logger.info(f"Stopped database sync for Neovim instance: {instance_id}")
        return True
    
    async def _sync_loop(self, instance_id: str, neovim_api_base: str):
        """Sync loop for a Neovim instance."""
        while True:
            try:
                response = requests.get(
                    f"{neovim_api_base}/state",
                    params={"id": instance_id}
                )
                
                if response.status_code == 200:
                    neovim_state = response.json()
                    
                    state = NeovimStateModel(
                        instance_id=instance_id,
                        buffers=neovim_state.get("buffers", []),
                        cursor_positions=neovim_state.get("cursor_positions", {}),
                        registers=neovim_state.get("registers", {}),
                        marks=neovim_state.get("marks", {}),
                        options=neovim_state.get("options", {}),
                        last_updated=int(neovim_state.get("timestamp", 0)),
                        active=True
                    )
                    
                    self.db_client.save_state(state)
                
                else:
                    logger.warning(f"Failed to get Neovim state: {response.text}")
            
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
            
            await asyncio.sleep(self.sync_interval)
    
    async def restore_state(self, instance_id: str, neovim_api_base: str) -> bool:
        """Restore a Neovim instance state from the database."""
        try:
            state = self.db_client.load_state(instance_id)
            if not state:
                logger.warning(f"No state found for Neovim instance: {instance_id}")
                return False
            
            neovim_state = {
                "buffers": state.buffers,
                "cursor_positions": state.cursor_positions,
                "registers": state.registers,
                "marks": state.marks,
                "options": state.options
            }
            
            response = requests.post(
                f"{neovim_api_base}/restore",
                json={"id": instance_id, "state": neovim_state}
            )
            
            if response.status_code == 200:
                logger.info(f"Restored state for Neovim instance: {instance_id}")
                return True
            else:
                logger.error(f"Failed to restore Neovim state: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error restoring state: {e}")
            return False
    
    async def list_instances(self, active_only: bool = True) -> List[str]:
        """List all Neovim instances in the database."""
        states = self.db_client.list_states(active_only)
        return [state.instance_id for state in states]
    
    async def cleanup(self):
        """Clean up all sync tasks."""
        for instance_id, task in list(self._sync_tasks.items()):
            await self.stop_sync(instance_id)
        
        logger.info("Cleaned up all database sync tasks")

neovim_db_integration = NeovimDatabaseIntegration()
