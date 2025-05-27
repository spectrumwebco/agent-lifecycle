"""
Base Go integration for Python agents.

This module provides base Go integration components that can be used by both
Kled and Veigar agents.
"""

import json
import logging
import os
import socket
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import grpc
import requests

logger = logging.getLogger(__name__)

class BaseGoIntegration:
    """Base class for Go integration."""
    
    def __init__(self, agent_name: str, grpc_port: int = 50051, socket_io_port: int = 8080):
        """
        Initialize the base Go integration.
        
        Args:
            agent_name: Name of the agent.
            grpc_port: Port for gRPC communication.
            socket_io_port: Port for Socket.IO communication.
        """
        self.agent_name = agent_name
        self.grpc_port = grpc_port
        self.socket_io_port = socket_io_port
        self.grpc_channel = None
        self.event_handlers = {}
        self.state_handlers = {}
        
        logger.info(f"Initialized {agent_name} Go integration")
    
    def start_grpc_client(self) -> bool:
        """
        Start the gRPC client.
        
        Returns:
            True if the client was started successfully, False otherwise.
        """
        try:
            self.grpc_channel = grpc.insecure_channel(f"localhost:{self.grpc_port}")
            logger.info(f"Started gRPC client for {self.agent_name} on port {self.grpc_port}")
            return True
        except Exception as e:
            logger.exception(f"Error starting gRPC client for {self.agent_name}")
            return False
    
    def stop_grpc_client(self) -> None:
        """Stop the gRPC client."""
        if self.grpc_channel:
            self.grpc_channel.close()
            self.grpc_channel = None
            logger.info(f"Stopped gRPC client for {self.agent_name}")
    
    def send_event(self, event_type: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Send an event to the Go service.
        
        Args:
            event_type: Type of the event.
            data: Event data.
            
        Returns:
            A tuple containing a success flag and a message.
        """
        try:
            
            response = requests.post(
                f"http://localhost:{self.socket_io_port}/events",
                json={
                    "type": event_type,
                    "data": data
                }
            )
            
            if response.status_code == 200:
                return True, "Event sent successfully"
            else:
                return False, f"Error sending event: {response.text}"
        except Exception as e:
            logger.exception(f"Error sending event to Go service")
            return False, str(e)
    
    def get_state(self, state_type: str, state_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get state from the Go service.
        
        Args:
            state_type: Type of the state.
            state_id: ID of the state.
            
        Returns:
            A tuple containing a success flag, a message, and the state data (if successful).
        """
        try:
            
            response = requests.get(
                f"http://localhost:{self.socket_io_port}/state",
                params={
                    "type": state_type,
                    "id": state_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, "State retrieved successfully", data.get("state")
            else:
                return False, f"Error getting state: {response.text}", None
        except Exception as e:
            logger.exception(f"Error getting state from Go service")
            return False, str(e), None
    
    def set_state(self, state_type: str, state_id: str, state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Set state in the Go service.
        
        Args:
            state_type: Type of the state.
            state_id: ID of the state.
            state: State data.
            
        Returns:
            A tuple containing a success flag and a message.
        """
        try:
            
            response = requests.post(
                f"http://localhost:{self.socket_io_port}/state",
                json={
                    "type": state_type,
                    "id": state_id,
                    "state": state
                }
            )
            
            if response.status_code == 200:
                return True, "State set successfully"
            else:
                return False, f"Error setting state: {response.text}"
        except Exception as e:
            logger.exception(f"Error setting state in Go service")
            return False, str(e)
    
    def register_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a handler for events.
        
        Args:
            event_type: Type of the event.
            handler: Event handler function.
        """
        self.event_handlers[event_type] = handler
        logger.info(f"Registered handler for event type '{event_type}'")
    
    def register_state_handler(self, state_type: str, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Register a handler for state changes.
        
        Args:
            state_type: Type of the state.
            handler: State handler function.
        """
        self.state_handlers[state_type] = handler
        logger.info(f"Registered handler for state type '{state_type}'")
    
    def start_event_listener(self) -> threading.Thread:
        """
        Start a thread to listen for events from the Go service.
        
        Returns:
            The event listener thread.
        """
        def listener_thread():
            logger.info(f"Started event listener for {self.agent_name}")
            
            
            while True:
                time.sleep(1)  # Avoid busy waiting
        
        thread = threading.Thread(target=listener_thread, daemon=True)
        thread.start()
        
        return thread
    
    def start_go_service(self, executable_path: str, args: Optional[List[str]] = None) -> subprocess.Popen:
        """
        Start the Go service.
        
        Args:
            executable_path: Path to the Go executable.
            args: Command-line arguments for the executable.
            
        Returns:
            The subprocess object for the Go service.
        """
        if args is None:
            args = []
        
        try:
            process = subprocess.Popen(
                [executable_path] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            logger.info(f"Started Go service for {self.agent_name} with PID {process.pid}")
            return process
        except Exception as e:
            logger.exception(f"Error starting Go service for {self.agent_name}")
            raise
    
    def stop_go_service(self, process: subprocess.Popen) -> None:
        """
        Stop the Go service.
        
        Args:
            process: The subprocess object for the Go service.
        """
        if process.poll() is None:  # Process is still running
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            logger.info(f"Stopped Go service for {self.agent_name} with PID {process.pid}")
