"""
Integration module for connecting the Django app with the Go codebase.
This module provides utilities for interacting with the Go runtime from Python.
"""

import os
import json
import time
import uuid
import logging
import threading
import grpc
from typing import Dict, Any, List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.cache import cache

from .grpc_client import agent_pb2, agent_pb2_grpc

logger = logging.getLogger(__name__)

class GoRuntimeIntegration:
    """
    Integration class for connecting the Django app with the Go runtime.
    Provides methods for executing tasks, managing state, and handling events.
    """
    
    def __init__(self, 
                 grpc_host: Optional[str] = None, 
                 grpc_port: Optional[int] = None,
                 connection_timeout: int = 30,
                 reconnect_attempts: int = 5,
                 reconnect_delay: int = 5,
                 enable_langsmith: bool = True,
                 langsmith_project: str = "django-go-integration"):
        """
        Initialize the Go runtime integration.
        
        Args:
            grpc_host: Host address for the gRPC server
            grpc_port: Port for the gRPC server
            connection_timeout: Timeout for connection attempts in seconds
            reconnect_attempts: Number of reconnection attempts
            reconnect_delay: Delay between reconnection attempts in seconds
            enable_langsmith: Whether to enable LangSmith integration
            langsmith_project: LangSmith project name
        """
        self.grpc_host = grpc_host or os.environ.get("GO_RUNTIME_HOST", "localhost")
        self.grpc_port = grpc_port or int(os.environ.get("GO_RUNTIME_PORT", "50051"))
        self.connection_timeout = connection_timeout
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.enable_langsmith = enable_langsmith
        self.langsmith_project = langsmith_project
        
        self.channel = None
        self.stub = None
        self.connected = False
        self.session_id = str(uuid.uuid4())
        
        self.event_handlers = {}
        self.event_listener_thread = None
        self.event_listener_running = False
        
        self.connect()
    
    def connect(self) -> bool:
        """
        Connect to the Go runtime via gRPC.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self.connected:
            return True
        
        for attempt in range(self.reconnect_attempts):
            try:
                self.channel = grpc.insecure_channel(f"{self.grpc_host}:{self.grpc_port}")
                
                self.stub = agent_pb2_grpc.AgentServiceStub(self.channel)
                
                request = agent_pb2.HealthCheckRequest(session_id=self.session_id)
                response = self.stub.HealthCheck(request, timeout=self.connection_timeout)
                
                if response.status == agent_pb2.HealthCheckResponse.Status.SERVING:
                    self.connected = True
                    logger.info(f"Connected to Go runtime at {self.grpc_host}:{self.grpc_port}")
                    
                    self._start_event_listener()
                    
                    return True
                else:
                    logger.warning(f"Go runtime is not serving: {response.status}")
            except grpc.RpcError as e:
                logger.warning(f"Failed to connect to Go runtime (attempt {attempt+1}/{self.reconnect_attempts}): {e}")
                time.sleep(self.reconnect_delay)
        
        logger.error(f"Failed to connect to Go runtime after {self.reconnect_attempts} attempts")
        return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the Go runtime.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if not self.connected:
            return True
        
        try:
            self._stop_event_listener()
            
            if self.channel:
                self.channel.close()
                self.channel = None
                self.stub = None
            
            self.connected = False
            logger.info("Disconnected from Go runtime")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Go runtime: {e}")
            return False
    
    def execute_task(self, 
                     task_type: str, 
                     input_data: Dict[str, Any], 
                     agent_id: Optional[str] = None,
                     task_id: Optional[str] = None,
                     description: Optional[str] = None,
                     timeout: int = 60,
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task in the Go runtime.
        
        Args:
            task_type: Type of the task
            input_data: Input data for the task
            agent_id: ID of the agent to execute the task
            task_id: ID of the task (generated if not provided)
            description: Description of the task
            timeout: Timeout for the task execution in seconds
            metadata: Metadata for the task
            
        Returns:
            Dict[str, Any]: Result of the task execution
        """
        if not self.connected and not self.connect():
            raise ConnectionError("Not connected to Go runtime")
        
        task_id = task_id or str(uuid.uuid4())
        
        try:
            input_json = json.dumps(input_data)
            metadata_json = json.dumps(metadata or {})
            
            request = agent_pb2.ExecuteTaskRequest(
                session_id=self.session_id,
                task_id=task_id,
                task_type=task_type,
                description=description or f"Task {task_type}",
                input=input_json,
                agent_id=agent_id or "",
                timeout=timeout,
                metadata=metadata_json
            )
            
            if self.stub is None:
                raise ConnectionError("gRPC stub is not initialized")
                
            response = self.stub.ExecuteTask(request, timeout=timeout + 10)
            
            result = {
                "task_id": response.task_id,
                "agent_id": response.agent_id,
                "status": response.status,
                "output": json.loads(response.output) if response.output else {},
                "error": response.error,
                "execution_time": response.execution_time,
                "metadata": json.loads(response.metadata) if response.metadata else {}
            }
            
            return result
        except grpc.RpcError as e:
            logger.error(f"Failed to execute task: {e}")
            
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.connected = False
                if self.connect():
                    return self.execute_task(
                        task_type=task_type,
                        input_data=input_data,
                        agent_id=agent_id,
                        task_id=task_id,
                        description=description,
                        timeout=timeout,
                        metadata=metadata
                    )
            
            return {
                "task_id": task_id,
                "agent_id": agent_id or "",
                "status": "error",
                "output": {},
                "error": str(e),
                "execution_time": 0,
                "metadata": metadata or {}
            }
    
    def execute_agent_task(self, 
                          agent_id: str,
                          task_type: str,
                          input_data: Dict[str, Any],
                          task_id: Optional[str] = None,
                          description: Optional[str] = None,
                          timeout: int = 60,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task using a specific agent in the multi-agent system.
        
        Args:
            agent_id: ID of the agent to execute the task
            task_type: Type of the task
            input_data: Input data for the task
            task_id: ID of the task (generated if not provided)
            description: Description of the task
            timeout: Timeout for the task execution in seconds
            metadata: Metadata for the task
            
        Returns:
            Dict[str, Any]: Result of the task execution
        """
        if not self.connected and not self.connect():
            raise ConnectionError("Not connected to Go runtime")
        
        task_id = task_id or str(uuid.uuid4())
        
        try:
            input_json = json.dumps(input_data)
            metadata_json = json.dumps(metadata or {})
            
            request = agent_pb2.ExecuteAgentTaskRequest(
                session_id=self.session_id,
                task_id=task_id,
                agent_id=agent_id,
                task_type=task_type,
                description=description or f"Agent task {task_type}",
                input=input_json,
                timeout=timeout,
                metadata=metadata_json
            )
            
            if self.stub is None:
                raise ConnectionError("gRPC stub is not initialized")
                
            response = self.stub.ExecuteAgentTask(request, timeout=timeout + 10)
            
            result = {
                "task_id": response.task_id,
                "agent_id": response.agent_id,
                "status": response.status,
                "output": json.loads(response.output) if response.output else {},
                "error": response.error,
                "execution_time": response.execution_time,
                "metadata": json.loads(response.metadata) if response.metadata else {}
            }
            
            return result
        except grpc.RpcError as e:
            logger.error(f"Failed to execute agent task: {e}")
            
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.connected = False
                if self.connect():
                    return self.execute_agent_task(
                        agent_id=agent_id,
                        task_type=task_type,
                        input_data=input_data,
                        task_id=task_id,
                        description=description,
                        timeout=timeout,
                        metadata=metadata
                    )
            
            return {
                "task_id": task_id,
                "agent_id": agent_id,
                "status": "error",
                "output": {},
                "error": str(e),
                "execution_time": 0,
                "metadata": metadata or {}
            }
    
    def get_state(self, key: str) -> Any:
        """
        Get a value from the shared state.
        
        Args:
            key: Key of the value to get
            
        Returns:
            Any: Value from the shared state
        """
        if not self.connected and not self.connect():
            raise ConnectionError("Not connected to Go runtime")
        
        try:
            request = agent_pb2.GetStateRequest(
                session_id=self.session_id,
                key=key
            )
            
            if self.stub is None:
                raise ConnectionError("gRPC stub is not initialized")
                
            response = self.stub.GetState(request)
            
            if not response.found:
                return None
            
            return json.loads(response.value) if response.value else None
        except grpc.RpcError as e:
            logger.error(f"Failed to get state: {e}")
            
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.connected = False
                if self.connect():
                    return self.get_state(key)
            
            return None
    
    def set_state(self, key: str, value: Any) -> bool:
        """
        Set a value in the shared state.
        
        Args:
            key: Key of the value to set
            value: Value to set
            
        Returns:
            bool: True if the value was set successfully, False otherwise
        """
        if not self.connected and not self.connect():
            raise ConnectionError("Not connected to Go runtime")
        
        try:
            value_json = json.dumps(value)
            
            request = agent_pb2.SetStateRequest(
                session_id=self.session_id,
                key=key,
                value=value_json
            )
            
            if self.stub is None:
                raise ConnectionError("gRPC stub is not initialized")
                
            response = self.stub.SetState(request)
            
            return response.success
        except grpc.RpcError as e:
            logger.error(f"Failed to set state: {e}")
            
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.connected = False
                if self.connect():
                    return self.set_state(key, value)
            
            return False
    
    def delete_state(self, key: str) -> bool:
        """
        Delete a value from the shared state.
        
        Args:
            key: Key of the value to delete
            
        Returns:
            bool: True if the value was deleted successfully, False otherwise
        """
        if not self.connected and not self.connect():
            raise ConnectionError("Not connected to Go runtime")
        
        try:
            request = agent_pb2.DeleteStateRequest(
                session_id=self.session_id,
                key=key
            )
            
            if self.stub is None:
                raise ConnectionError("gRPC stub is not initialized")
                
            response = self.stub.DeleteState(request)
            
            return response.success
        except grpc.RpcError as e:
            logger.error(f"Failed to delete state: {e}")
            
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.connected = False
                if self.connect():
                    return self.delete_state(key)
            
            return False
    
    def subscribe_to_events(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subscribe to events of the specified type.
        
        Args:
            event_type: Type of events to subscribe to
            handler: Handler function to call when an event is received
            
        Returns:
            str: Subscription ID
        """
        subscription_id = str(uuid.uuid4())
        
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = {}
        
        self.event_handlers[event_type][subscription_id] = handler
        
        return subscription_id
    
    def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID to unsubscribe
            
        Returns:
            bool: True if the subscription was removed successfully, False otherwise
        """
        for event_type, handlers in self.event_handlers.items():
            if subscription_id in handlers:
                del handlers[subscription_id]
                if not handlers:
                    del self.event_handlers[event_type]
                return True
        
        return False
    
    def publish_event(self, 
                     event_type: str, 
                     data: Dict[str, Any], 
                     source: str = "django", 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish an event.
        
        Args:
            event_type: Type of the event
            data: Data for the event
            source: Source of the event
            metadata: Metadata for the event
            
        Returns:
            bool: True if the event was published successfully, False otherwise
        """
        if not self.connected and not self.connect():
            raise ConnectionError("Not connected to Go runtime")
        
        try:
            data_json = json.dumps(data)
            metadata_json = json.dumps(metadata or {})
            
            request = agent_pb2.PublishEventRequest(
                session_id=self.session_id,
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                source=source,
                timestamp=int(time.time() * 1000),
                data=data_json,
                metadata=metadata_json
            )
            
            if self.stub is None:
                raise ConnectionError("gRPC stub is not initialized")
                
            response = self.stub.PublishEvent(request)
            
            return response.success
        except grpc.RpcError as e:
            logger.error(f"Failed to publish event: {e}")
            
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.connected = False
                if self.connect():
                    return self.publish_event(
                        event_type=event_type,
                        data=data,
                        source=source,
                        metadata=metadata
                    )
            
            return False
    
    def _start_event_listener(self):
        """
        Start the event listener thread.
        """
        if self.event_listener_thread and self.event_listener_thread.is_alive():
            return
        
        self.event_listener_running = True
        self.event_listener_thread = threading.Thread(target=self._event_listener_loop)
        self.event_listener_thread.daemon = True
        self.event_listener_thread.start()
    
    def _stop_event_listener(self):
        """
        Stop the event listener thread.
        """
        self.event_listener_running = False
        
        if self.event_listener_thread:
            self.event_listener_thread.join(timeout=5)
            self.event_listener_thread = None
    
    def _event_listener_loop(self):
        """
        Event listener loop.
        """
        while self.event_listener_running and self.connected:
            try:
                request = agent_pb2.SubscribeToEventsRequest(
                    session_id=self.session_id,
                    event_types=list(self.event_handlers.keys())
                )
                
                if self.stub is None:
                    raise ConnectionError("gRPC stub is not initialized")
                    
                for event in self.stub.SubscribeToEvents(request):
                    event_data = {
                        "id": event.event_id,
                        "type": event.event_type,
                        "source": event.source,
                        "timestamp": event.timestamp,
                        "data": json.loads(event.data) if event.data else {},
                        "metadata": json.loads(event.metadata) if event.metadata else {}
                    }
                    
                    if event.event_type in self.event_handlers:
                        for handler in self.event_handlers[event.event_type].values():
                            try:
                                handler(event_data)
                            except Exception as e:
                                logger.error(f"Error in event handler: {e}")
            except grpc.RpcError as e:
                logger.error(f"Error in event listener: {e}")
                
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    self.connected = False
                    if not self.connect():
                        time.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Unexpected error in event listener: {e}")
                time.sleep(1)
    
    def __del__(self):
        """
        Clean up resources when the object is deleted.
        """
        self.disconnect()


_go_runtime_integration = None

def get_go_runtime_integration() -> GoRuntimeIntegration:
    """
    Get the singleton instance of the Go runtime integration.
    
    Returns:
        GoRuntimeIntegration: Singleton instance of the Go runtime integration
    """
    global _go_runtime_integration
    
    if _go_runtime_integration is None:
        config = getattr(settings, "GO_RUNTIME_INTEGRATION", {})
        
        _go_runtime_integration = GoRuntimeIntegration(
            grpc_host=config.get("host"),
            grpc_port=config.get("port"),
            connection_timeout=config.get("connection_timeout", 30),
            reconnect_attempts=config.get("reconnect_attempts", 5),
            reconnect_delay=config.get("reconnect_delay", 5),
            enable_langsmith=config.get("enable_langsmith", True),
            langsmith_project=config.get("langsmith_project", "django-go-integration")
        )
    
    return _go_runtime_integration
