"""
Mock database implementations for local development and testing.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MockSupabaseClient:
    """Mock Supabase client for testing."""
    
    def __init__(self, url="mock://supabase", key="mock-key", database="default", mock=True):
        self.url = url
        self.key = key
        self.database = database
        self.mock = mock
        self.data = {}
        logger.info(f"Initialized MockSupabaseClient for {database}")
    
    def query_table(self, table_name):
        """Query a table."""
        if table_name not in self.data:
            self.data[table_name] = []
        return self.data[table_name]
    
    def insert_record(self, table_name, record):
        """Insert a record into a table."""
        if table_name not in self.data:
            self.data[table_name] = []
        record["id"] = len(self.data[table_name]) + 1
        self.data[table_name].append(record)
        return record

class MockRAGflowClient:
    """Mock RAGflow client for testing."""
    
    def __init__(self, host="localhost", port=8080, api_key="mock-key", mock=True):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.mock = mock
        logger.info(f"Initialized MockRAGflowClient")
    
    def search(self, query, top_k=5):
        """Search for vectors."""
        return {"results": [{"content": f"Result for {query}", "score": 0.9}]}
    
    def semantic_search(self, query, top_k=5):
        """Perform semantic search."""
        return {"results": [{"content": f"Semantic result for {query}", "score": 0.95}]}

class MockDragonflyClient:
    """Mock DragonflyDB client for testing."""
    
    def __init__(self, host="localhost", port=6379, password="", mock=True):
        self.host = host
        self.port = port
        self.password = password
        self.mock = mock
        self.data = {}
        self.memcached_data = {}
        logger.info(f"Initialized MockDragonflyClient")
    
    def set(self, key, value):
        """Set a key-value pair."""
        self.data[key] = value
        return True
    
    def get(self, key):
        """Get a value by key."""
        return self.data.get(key)
    
    def memcached_set(self, key, value):
        """Set a key-value pair using memcached protocol."""
        self.memcached_data[key] = value
        return True
    
    def memcached_get(self, key):
        """Get a value by key using memcached protocol."""
        return self.memcached_data.get(key)

class MockRocketMQClient:
    """Mock RocketMQ client for testing."""
    
    def __init__(self, host="localhost", port=9876, group="default", mock=True):
        self.host = host
        self.port = port
        self.group = group
        self.mock = mock
        self.messages = {}
        self.states = {}
        logger.info(f"Initialized MockRocketMQClient")
    
    def send_message(self, topic, message):
        """Send a message to a topic."""
        if topic not in self.messages:
            self.messages[topic] = []
        message_id = f"msg_{len(self.messages[topic]) + 1}"
        self.messages[topic].append({"id": message_id, "data": message})
        return message_id
    
    def consume_message(self, topic, timeout=0):
        """Consume a message from a topic."""
        if topic not in self.messages or not self.messages[topic]:
            return None
        return self.messages[topic].pop(0)
    
    def update_state(self, state_key, state_value):
        """Update a state."""
        self.states[state_key] = state_value
        return True
    
    def get_state(self, state_key):
        """Get a state."""
        return self.states.get(state_key, {})

class MockDorisClient:
    """Mock Apache Doris client for testing."""
    
    def __init__(self, connection_params=None, mock=True):
        self.connection_params = connection_params or {}
        self.mock = mock
        self.tables = {}
        logger.info(f"Initialized MockDorisClient")
    
    def execute_query(self, query):
        """Execute a query."""
        return [{"result": "success"}]
    
    def create_table(self, table_name, schema):
        """Create a table."""
        self.tables[table_name] = {"schema": schema, "data": []}
        return True
    
    def insert_data(self, table_name, data):
        """Insert data into a table."""
        if table_name not in self.tables:
            return 0
        self.tables[table_name]["data"].extend(data)
        return len(data)

class MockKafkaClient:
    """Mock Apache Kafka client for testing."""
    
    def __init__(self, bootstrap_servers="localhost:9092", group_id="default", mock=True):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.mock = mock
        self.messages = {}
        logger.info(f"Initialized MockKafkaClient")
    
    def produce_message(self, topic, message):
        """Produce a message to a topic."""
        if topic not in self.messages:
            self.messages[topic] = []
        self.messages[topic].append({"value": message})
        return True
    
    def consume_message(self, topic, timeout=0):
        """Consume a message from a topic."""
        if topic not in self.messages or not self.messages[topic]:
            return None
        return self.messages[topic].pop(0)

class MockPostgresClient:
    """Mock PostgreSQL client for testing."""
    
    def __init__(self, host="localhost", port=5432, user="postgres", password="", database="postgres", mock=True):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.mock = mock
        self.tables = {}
        logger.info(f"Initialized MockPostgresClient for {database}")
    
    def execute_query(self, query):
        """Execute a query."""
        return [{"result": "success"}]
    
    def create_table(self, table_name, schema):
        """Create a table."""
        self.tables[table_name] = {"schema": schema, "data": []}
        return True
    
    def insert_data(self, table_name, data):
        """Insert data into a table."""
        if table_name not in self.tables:
            return 0
        self.tables[table_name]["data"].extend(data)
        return len(data)
