"""
RocketMQ integration for the python_agent app.

This module provides integration with RocketMQ message queue,
enabling state communication between components.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Union, Callable
from django.conf import settings
from enum import Enum

logger = logging.getLogger(__name__)

class ConsumeStatus(Enum):
    CONSUME_SUCCESS = 0
    RECONSUME_LATER = 1

try:
    from rocketmq.client import Producer, PushConsumer
    from rocketmq.client import ConsumeStatus as RocketMQConsumeStatus
    ConsumeStatus = RocketMQConsumeStatus
    ROCKETMQ_AVAILABLE = True
except ImportError:
    logger.warning("RocketMQ Python client not available. Using mock implementation.")
    ROCKETMQ_AVAILABLE = False


class RocketMQClient:
    """
    Client for interacting with RocketMQ.
    
    This client provides methods for producing and consuming messages
    in RocketMQ, enabling state communication between components.
    """
    
    def __init__(self, host=None, port=None, group_id="python_agent"):
        """
        Initialize the RocketMQ client.
        
        Args:
            host: RocketMQ host
            port: RocketMQ port
            group_id: Producer and consumer group ID
        """
        rocketmq_config = getattr(settings, 'ROCKETMQ_CONFIG', {})
        
        self.host = host or rocketmq_config.get('host', 'localhost')
        self.port = port or rocketmq_config.get('port', 9876)
        self.group_id = group_id
        self.name_server_address = f"{self.host}:{self.port}"
        
        self.producers = {}
        self.consumers = {}
    
    def create_producer(self, topic: str) -> bool:
        """
        Create a producer for a topic.
        
        Args:
            topic: Topic to produce messages to
            
        Returns:
            bool: True if the producer was created successfully, False otherwise
        """
        if not ROCKETMQ_AVAILABLE:
            logger.warning(f"RocketMQ Python client not available. Mock producer created for topic {topic}.")
            self.producers[topic] = MockProducer(topic)
            return True
        
        try:
            producer = Producer(self.group_id)
            producer.set_name_server_address(self.name_server_address)
            producer.set_session_credentials(
                "access_key", "secret_key", "ALIYUN"
            )
            producer.start()
            
            self.producers[topic] = producer
            
            return True
        
        except Exception as e:
            logger.error(f"Error creating producer for topic {topic}: {e}")
            return False
    
    def create_consumer(self, topic: str, callback: Callable[[str, str], ConsumeStatus]) -> bool:
        """
        Create a consumer for a topic.
        
        Args:
            topic: Topic to consume messages from
            callback: Callback function to handle messages
            
        Returns:
            bool: True if the consumer was created successfully, False otherwise
        """
        if not ROCKETMQ_AVAILABLE:
            logger.warning(f"RocketMQ Python client not available. Mock consumer created for topic {topic}.")
            self.consumers[topic] = MockConsumer(topic, callback)
            return True
        
        try:
            consumer = PushConsumer(self.group_id)
            consumer.set_name_server_address(self.name_server_address)
            consumer.set_session_credentials(
                "access_key", "secret_key", "ALIYUN"
            )
            consumer.subscribe(topic, callback)
            consumer.start()
            
            self.consumers[topic] = consumer
            
            return True
        
        except Exception as e:
            logger.error(f"Error creating consumer for topic {topic}: {e}")
            return False
    
    def send_message(self, topic: str, message: str, tags: str = None, keys: str = None) -> bool:
        """
        Send a message to a topic.
        
        Args:
            topic: Topic to send the message to
            message: Message to send
            tags: Message tags
            keys: Message keys
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        if topic not in self.producers:
            if not self.create_producer(topic):
                return False
        
        try:
            producer = self.producers[topic]
            
            if isinstance(producer, MockProducer):
                return producer.send_sync(message, tags, keys)
            
            send_result = producer.send_sync(
                topic,
                message,
                tags=tags or "",
                keys=keys or ""
            )
            
            return send_result.status == 0
        
        except Exception as e:
            logger.error(f"Error sending message to topic {topic}: {e}")
            return False
    
    def send_json(self, topic: str, data: Dict[str, Any], tags: str = None, keys: str = None) -> bool:
        """
        Send a JSON message to a topic.
        
        Args:
            topic: Topic to send the message to
            data: JSON data to send
            tags: Message tags
            keys: Message keys
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        try:
            message = json.dumps(data)
            return self.send_message(topic, message, tags, keys)
        
        except Exception as e:
            logger.error(f"Error sending JSON message to topic {topic}: {e}")
            return False
    
    def shutdown(self):
        """
        Shutdown all producers and consumers.
        """
        for topic, producer in self.producers.items():
            try:
                if not isinstance(producer, MockProducer):
                    producer.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down producer for topic {topic}: {e}")
        
        for topic, consumer in self.consumers.items():
            try:
                if not isinstance(consumer, MockConsumer):
                    consumer.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down consumer for topic {topic}: {e}")
        
        self.producers = {}
        self.consumers = {}


class MockProducer:
    """
    Mock implementation of RocketMQ Producer.
    
    This class provides a mock implementation of the RocketMQ Producer
    for use when the RocketMQ Python client is not available.
    """
    
    def __init__(self, topic: str):
        """
        Initialize the mock producer.
        
        Args:
            topic: Topic to produce messages to
        """
        self.topic = topic
        self.messages = []
    
    def send_sync(self, message: str, tags: str = None, keys: str = None) -> bool:
        """
        Send a message synchronously.
        
        Args:
            message: Message to send
            tags: Message tags
            keys: Message keys
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        self.messages.append({
            'message': message,
            'tags': tags,
            'keys': keys,
            'timestamp': time.time()
        })
        
        logger.info(f"Mock producer sent message to topic {self.topic}: {message}")
        
        return True


class MockConsumer:
    """
    Mock implementation of RocketMQ Consumer.
    
    This class provides a mock implementation of the RocketMQ Consumer
    for use when the RocketMQ Python client is not available.
    """
    
    def __init__(self, topic: str, callback: Callable[[str, str], Any]):
        """
        Initialize the mock consumer.
        
        Args:
            topic: Topic to consume messages from
            callback: Callback function to handle messages
        """
        self.topic = topic
        self.callback = callback
    
    def subscribe(self, topic: str, callback: Callable[[str, str], Any]):
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function to handle messages
        """
        self.topic = topic
        self.callback = callback
    
    def start(self):
        """
        Start the consumer.
        """
        logger.info(f"Mock consumer started for topic {self.topic}")
    
    def shutdown(self):
        """
        Shutdown the consumer.
        """
        logger.info(f"Mock consumer shutdown for topic {self.topic}")


class StateManager:
    """
    State manager for the python_agent app.
    
    This class provides methods for managing state using RocketMQ
    for communication between components.
    """
    
    def __init__(self, client: RocketMQClient = None):
        """
        Initialize the state manager.
        
        Args:
            client: RocketMQ client
        """
        self.client = client or RocketMQClient()
        self.state_topic = "python_agent_state"
        self.state_handlers = {}
        
        self.client.create_producer(self.state_topic)
    
    def register_state_handler(self, state_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Register a handler for a state type.
        
        Args:
            state_type: Type of state to handle
            handler: Handler function
        """
        self.state_handlers[state_type] = handler
    
    def update_state(self, state_type: str, state_id: str, data: Dict[str, Any]) -> bool:
        """
        Update state.
        
        Args:
            state_type: Type of state to update
            state_id: ID of the state to update
            data: State data
            
        Returns:
            bool: True if the state was updated successfully, False otherwise
        """
        message = {
            'type': 'state_update',
            'state_type': state_type,
            'state_id': state_id,
            'data': data,
            'timestamp': time.time()
        }
        
        return self.client.send_json(self.state_topic, message, tags=state_type, keys=state_id)
    
    def handle_message(self, topic: str, message: str) -> Any:
        """
        Handle a message from RocketMQ.
        
        Args:
            topic: Topic the message was received from
            message: Message received
            
        Returns:
            Any: Result of handling the message
        """
        try:
            data = json.loads(message)
            
            if data.get('type') == 'state_update':
                state_type = data.get('state_type')
                
                if state_type in self.state_handlers:
                    self.state_handlers[state_type](data)
            
            return ConsumeStatus.CONSUME_SUCCESS if ROCKETMQ_AVAILABLE else True
        
        except Exception as e:
            logger.error(f"Error handling message from topic {topic}: {e}")
            return ConsumeStatus.RECONSUME_LATER if ROCKETMQ_AVAILABLE else False
    
    def start_consumer(self) -> bool:
        """
        Start the state consumer.
        
        Returns:
            bool: True if the consumer was started successfully, False otherwise
        """
        return self.client.create_consumer(self.state_topic, self.handle_message)
    
    def shutdown(self):
        """
        Shutdown the state manager.
        """
        self.client.shutdown()


rocketmq_client = RocketMQClient()

state_manager = StateManager(rocketmq_client)
