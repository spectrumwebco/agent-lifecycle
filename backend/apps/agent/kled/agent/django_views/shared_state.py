"""
Integration with the shared state system for the Python agent.

This module provides integration with the shared state system,
enabling the Python agent to interact with the Go framework.
"""

import json
import logging
from typing import Dict, Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class AgentSharedState:
    """
    Integration with the shared state system for the Python agent.
    
    This class provides methods for interacting with the shared state
    system, enabling the Python agent to communicate with the Go framework.
    """
    
    @staticmethod
    def get_state(state_id: str = 'default') -> Optional[Dict[str, Any]]:
        """
        Get the current state from the shared state system.
        
        Args:
            state_id: ID of the state to retrieve
            
        Returns:
            Dict[str, Any]: The current state, or None if an error occurred
        """
        try:
            from api.websocket_state import get_shared_state
            
            return get_shared_state(state_id)
        
        except Exception as e:
            logger.error(f"Error getting shared state: {e}")
            return None
    
    @staticmethod
    async def update_state(state_id: str, data: Dict[str, Any]) -> bool:
        """
        Update the state in the shared state system.
        
        Args:
            state_id: ID of the state to update
            data: New state data
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            from api.websocket_state import update_shared_state
            
            return await update_shared_state(state_id, data)
        
        except Exception as e:
            logger.error(f"Error updating shared state: {e}")
            return False
    
    @staticmethod
    def update_state_sync(state_id: str, data: Dict[str, Any]) -> bool:
        """
        Update the state in the shared state system synchronously.
        
        Args:
            state_id: ID of the state to update
            data: New state data
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            from api.grpc_bridge import grpc_bridge
            
            response = grpc_bridge.update_state(
                state_type='shared',
                state_id=state_id,
                data=data
            )
            
            return response.get('status') == 'success'
        
        except Exception as e:
            logger.error(f"Error updating shared state: {e}")
            return False
    
    @staticmethod
    def register_agent_with_state(agent_id: str, thread_id: str) -> bool:
        """
        Register an agent with the shared state system.
        
        This method registers an agent with the shared state system,
        enabling it to receive updates and notifications.
        
        Args:
            agent_id: ID of the agent to register
            thread_id: ID of the agent thread
            
        Returns:
            bool: True if the registration was successful, False otherwise
        """
        try:
            state = AgentSharedState.get_state('agents') or {}
            
            if 'agents' not in state:
                state['agents'] = {}
            
            state['agents'][agent_id] = {
                'thread_id': thread_id,
                'status': 'running',
                'last_updated': str(import_datetime().now().isoformat()),
            }
            
            return AgentSharedState.update_state_sync('agents', state)
        
        except Exception as e:
            logger.error(f"Error registering agent with state: {e}")
            return False
    
    @staticmethod
    def update_agent_status(agent_id: str, status: str) -> bool:
        """
        Update the status of an agent in the shared state system.
        
        Args:
            agent_id: ID of the agent to update
            status: New status of the agent
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            state = AgentSharedState.get_state('agents') or {}
            
            if 'agents' not in state or agent_id not in state['agents']:
                return False
            
            state['agents'][agent_id]['status'] = status
            state['agents'][agent_id]['last_updated'] = str(import_datetime().now().isoformat())
            
            return AgentSharedState.update_state_sync('agents', state)
        
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            return False
    
    @staticmethod
    def deregister_agent(agent_id: str) -> bool:
        """
        Deregister an agent from the shared state system.
        
        Args:
            agent_id: ID of the agent to deregister
            
        Returns:
            bool: True if the deregistration was successful, False otherwise
        """
        try:
            state = AgentSharedState.get_state('agents') or {}
            
            if 'agents' not in state or agent_id not in state['agents']:
                return False
            
            del state['agents'][agent_id]
            
            return AgentSharedState.update_state_sync('agents', state)
        
        except Exception as e:
            logger.error(f"Error deregistering agent: {e}")
            return False


def import_datetime():
    """Import datetime module to avoid circular imports."""
    import datetime
    return datetime
