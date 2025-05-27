"""
Shared state integration for Django.

This module provides integration with Kafka for shared state management
between different components of the system.
"""

import json
import logging
import threading
import time
from typing import Dict, Any, List, Optional, Union, Callable
from django.conf import settings
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SharedStateConfig(BaseModel):
    """Shared state configuration."""
    
    topic: str = Field(default="shared-state")
    poll_interval: float = Field(default=0.1)  # seconds
    use_mock: bool = Field(default=False)

class SharedState:
    """Shared state manager using Kafka."""
    
    def __init__(self, config: Optional[SharedStateConfig] = None, kafka_client=None):
        """Initialize the shared state manager."""
        self.config = config or self._get_default_config()
        self._kafka_client = kafka_client
        self._state = {}
        self._state_lock = threading.RLock()
        self._running = False
        self._consumer_thread = None
        self._state_handlers = []
        
        if not self._kafka_client:
            try:
                from .kafka import KafkaClient
                self._kafka_client = KafkaClient()
            except ImportError:
                logger.warning("Kafka client not available, using mock mode")
                self._use_mock = True
        
        self._use_mock = self.config.use_mock or getattr(self._kafka_client, '_use_mock', False)
        
        if self._use_mock:
            logger.warning("Shared state manager running in mock mode")
    
    def _get_default_config(self) -> SharedStateConfig:
        """Get the default configuration from settings."""
        return SharedStateConfig(
            topic=getattr(settings, 'SHARED_STATE_TOPIC', 'shared-state'),
            poll_interval=getattr(settings, 'SHARED_STATE_POLL_INTERVAL', 0.1),
            use_mock=getattr(settings, 'SHARED_STATE_USE_MOCK', False)
        )
    
    def _consumer_loop(self):
        """Consumer loop for processing state updates."""
        if self._use_mock:
            while self._running:
                time.sleep(1)
            return
        
        if not self._kafka_client:
            return
        
        self._kafka_client.subscribe([self.config.topic])
        
        self._kafka_client.register_handler(self.config.topic, self._handle_state_update)
        
        self._kafka_client.start_consumer()
        
        while self._running:
            time.sleep(1)
        
        self._kafka_client.stop_consumer()
    
    def _handle_state_update(self, message):
        """Handle a state update message."""
        try:
            state_update = message.value
            
            if not isinstance(state_update, dict):
                logger.warning(f"Invalid state update: {state_update}")
                return
            
            with self._state_lock:
                self._state.update(state_update)
            
            for handler in self._state_handlers:
                try:
                    handler(self._state)
                except Exception as e:
                    logger.error(f"Error in state handler: {e}")
        
        except Exception as e:
            logger.error(f"Error handling state update: {e}")
    
    def start(self) -> bool:
        """Start the shared state manager."""
        if self._running:
            logger.warning("Shared state manager already running")
            return True
        
        self._running = True
        
        self._consumer_thread = threading.Thread(target=self._consumer_loop)
        self._consumer_thread.daemon = True
        self._consumer_thread.start()
        
        logger.info(f"Started shared state manager with topic {self.config.topic}")
        return True
    
    def stop(self) -> bool:
        """Stop the shared state manager."""
        if not self._running:
            logger.warning("Shared state manager not running")
            return True
        
        self._running = False
        
        if self._consumer_thread:
            self._consumer_thread.join(timeout=5.0)
            self._consumer_thread = None
        
        logger.info("Stopped shared state manager")
        return True
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current state."""
        with self._state_lock:
            return self._state.copy()
    
    def update_state(self, state_update: Dict[str, Any]) -> bool:
        """Update the state."""
        if self._use_mock:
            with self._state_lock:
                self._state.update(state_update)
            
            for handler in self._state_handlers:
                try:
                    handler(self._state)
                except Exception as e:
                    logger.error(f"Error in state handler: {e}")
            
            return True
        
        if not self._kafka_client:
            logger.error("Kafka client not available")
            return False
        
        try:
            from .kafka import KafkaMessage
            
            message = KafkaMessage(
                topic=self.config.topic,
                value=state_update
            )
            
            result = self._kafka_client.produce(message)
            
            if result:
                with self._state_lock:
                    self._state.update(state_update)
                
                for handler in self._state_handlers:
                    try:
                        handler(self._state)
                    except Exception as e:
                        logger.error(f"Error in state handler: {e}")
            
            return result
        except Exception as e:
            logger.error(f"Error updating state: {e}")
            return False
    
    def register_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register a handler for state updates."""
        self._state_handlers.append(handler)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
