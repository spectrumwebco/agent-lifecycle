"""
DragonflyDB integration for the python_agent app.

This module provides integration with DragonflyDB (Redis-compatible database),
enabling caching and state management capabilities with Memcached support.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from django.conf import settings

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class DragonflyClient:
    """
    Client for interacting with DragonflyDB.
    
    This client provides methods for storing, retrieving, and managing
    data in DragonflyDB, which is Redis-compatible with Memcached support.
    """
    
    def __init__(self, host=None, port=None, db=None, password=None, use_ssl=None):
        """
        Initialize the DragonflyDB client.
        
        Args:
            host: DragonflyDB host
            port: DragonflyDB port
            db: DragonflyDB database number
            password: DragonflyDB password
            use_ssl: Whether to use SSL
        """
        redis_config = getattr(settings, 'REDIS_CONFIG', {})
        
        self.host = host or redis_config.get('host', 'localhost')
        self.port = port or redis_config.get('port', 6379)
        self.db = db or redis_config.get('db', 0)
        self.password = password or redis_config.get('password', '')
        self.use_ssl = use_ssl if use_ssl is not None else redis_config.get('use_ssl', False)
        
        self.client = self._create_client()
    
    def _create_client(self) -> redis.Redis:
        """
        Create a Redis client for DragonflyDB.
        
        Returns:
            redis.Redis: Redis client
        """
        try:
            return redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                ssl=self.use_ssl,
                decode_responses=True
            )
        
        except Exception as e:
            logger.error(f"Error creating DragonflyDB client: {e}")
            return None
    
    def get(self, key: str) -> Optional[str]:
        """
        Get a value from DragonflyDB.
        
        Args:
            key: Key to get
            
        Returns:
            Optional[str]: Value for the key, or None if the key does not exist
        """
        try:
            return self.client.get(key)
        
        except RedisError as e:
            logger.error(f"Error getting value from DragonflyDB: {e}")
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set a value in DragonflyDB.
        
        Args:
            key: Key to set
            value: Value to set
            ex: Expiration time in seconds
            
        Returns:
            bool: True if the value was set, False otherwise
        """
        try:
            return self.client.set(key, value, ex=ex)
        
        except RedisError as e:
            logger.error(f"Error setting value in DragonflyDB: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from DragonflyDB.
        
        Args:
            key: Key to delete
            
        Returns:
            bool: True if the key was deleted, False otherwise
        """
        try:
            return bool(self.client.delete(key))
        
        except RedisError as e:
            logger.error(f"Error deleting key from DragonflyDB: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in DragonflyDB.
        
        Args:
            key: Key to check
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        
        except RedisError as e:
            logger.error(f"Error checking if key exists in DragonflyDB: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set an expiration time for a key in DragonflyDB.
        
        Args:
            key: Key to set expiration for
            seconds: Expiration time in seconds
            
        Returns:
            bool: True if the expiration was set, False otherwise
        """
        try:
            return bool(self.client.expire(key, seconds))
        
        except RedisError as e:
            logger.error(f"Error setting expiration for key in DragonflyDB: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get the time to live for a key in DragonflyDB.
        
        Args:
            key: Key to get TTL for
            
        Returns:
            int: TTL in seconds, -1 if the key has no TTL, -2 if the key does not exist
        """
        try:
            return self.client.ttl(key)
        
        except RedisError as e:
            logger.error(f"Error getting TTL for key in DragonflyDB: {e}")
            return -2
    
    def keys(self, pattern: str = '*') -> List[str]:
        """
        Get keys matching a pattern from DragonflyDB.
        
        Args:
            pattern: Pattern to match
            
        Returns:
            List[str]: Keys matching the pattern
        """
        try:
            return self.client.keys(pattern)
        
        except RedisError as e:
            logger.error(f"Error getting keys from DragonflyDB: {e}")
            return []
    
    def hget(self, name: str, key: str) -> Optional[str]:
        """
        Get a value from a hash in DragonflyDB.
        
        Args:
            name: Hash name
            key: Key in the hash
            
        Returns:
            Optional[str]: Value for the key, or None if the key does not exist
        """
        try:
            return self.client.hget(name, key)
        
        except RedisError as e:
            logger.error(f"Error getting value from hash in DragonflyDB: {e}")
            return None
    
    def hset(self, name: str, key: str, value: str) -> bool:
        """
        Set a value in a hash in DragonflyDB.
        
        Args:
            name: Hash name
            key: Key in the hash
            value: Value to set
            
        Returns:
            bool: True if the value was set, False otherwise
        """
        try:
            return bool(self.client.hset(name, key, value))
        
        except RedisError as e:
            logger.error(f"Error setting value in hash in DragonflyDB: {e}")
            return False
    
    def hdel(self, name: str, key: str) -> bool:
        """
        Delete a key from a hash in DragonflyDB.
        
        Args:
            name: Hash name
            key: Key in the hash
            
        Returns:
            bool: True if the key was deleted, False otherwise
        """
        try:
            return bool(self.client.hdel(name, key))
        
        except RedisError as e:
            logger.error(f"Error deleting key from hash in DragonflyDB: {e}")
            return False
    
    def hkeys(self, name: str) -> List[str]:
        """
        Get keys in a hash in DragonflyDB.
        
        Args:
            name: Hash name
            
        Returns:
            List[str]: Keys in the hash
        """
        try:
            return self.client.hkeys(name)
        
        except RedisError as e:
            logger.error(f"Error getting keys from hash in DragonflyDB: {e}")
            return []
    
    def hgetall(self, name: str) -> Dict[str, str]:
        """
        Get all key-value pairs in a hash in DragonflyDB.
        
        Args:
            name: Hash name
            
        Returns:
            Dict[str, str]: Key-value pairs in the hash
        """
        try:
            return self.client.hgetall(name)
        
        except RedisError as e:
            logger.error(f"Error getting all key-value pairs from hash in DragonflyDB: {e}")
            return {}
    
    def lpush(self, name: str, *values: str) -> bool:
        """
        Push values to the head of a list in DragonflyDB.
        
        Args:
            name: List name
            values: Values to push
            
        Returns:
            bool: True if the values were pushed, False otherwise
        """
        try:
            return bool(self.client.lpush(name, *values))
        
        except RedisError as e:
            logger.error(f"Error pushing values to list in DragonflyDB: {e}")
            return False
    
    def rpush(self, name: str, *values: str) -> bool:
        """
        Push values to the tail of a list in DragonflyDB.
        
        Args:
            name: List name
            values: Values to push
            
        Returns:
            bool: True if the values were pushed, False otherwise
        """
        try:
            return bool(self.client.rpush(name, *values))
        
        except RedisError as e:
            logger.error(f"Error pushing values to list in DragonflyDB: {e}")
            return False
    
    def lpop(self, name: str) -> Optional[str]:
        """
        Pop a value from the head of a list in DragonflyDB.
        
        Args:
            name: List name
            
        Returns:
            Optional[str]: Value popped from the list, or None if the list is empty
        """
        try:
            return self.client.lpop(name)
        
        except RedisError as e:
            logger.error(f"Error popping value from list in DragonflyDB: {e}")
            return None
    
    def rpop(self, name: str) -> Optional[str]:
        """
        Pop a value from the tail of a list in DragonflyDB.
        
        Args:
            name: List name
            
        Returns:
            Optional[str]: Value popped from the list, or None if the list is empty
        """
        try:
            return self.client.rpop(name)
        
        except RedisError as e:
            logger.error(f"Error popping value from list in DragonflyDB: {e}")
            return None
    
    def lrange(self, name: str, start: int, end: int) -> List[str]:
        """
        Get a range of values from a list in DragonflyDB.
        
        Args:
            name: List name
            start: Start index
            end: End index
            
        Returns:
            List[str]: Values in the specified range
        """
        try:
            return self.client.lrange(name, start, end)
        
        except RedisError as e:
            logger.error(f"Error getting range from list in DragonflyDB: {e}")
            return []
    
    def llen(self, name: str) -> int:
        """
        Get the length of a list in DragonflyDB.
        
        Args:
            name: List name
            
        Returns:
            int: Length of the list
        """
        try:
            return self.client.llen(name)
        
        except RedisError as e:
            logger.error(f"Error getting length of list in DragonflyDB: {e}")
            return 0
    
    def sadd(self, name: str, *values: str) -> bool:
        """
        Add values to a set in DragonflyDB.
        
        Args:
            name: Set name
            values: Values to add
            
        Returns:
            bool: True if at least one value was added, False otherwise
        """
        try:
            return bool(self.client.sadd(name, *values))
        
        except RedisError as e:
            logger.error(f"Error adding values to set in DragonflyDB: {e}")
            return False
    
    def srem(self, name: str, *values: str) -> bool:
        """
        Remove values from a set in DragonflyDB.
        
        Args:
            name: Set name
            values: Values to remove
            
        Returns:
            bool: True if at least one value was removed, False otherwise
        """
        try:
            return bool(self.client.srem(name, *values))
        
        except RedisError as e:
            logger.error(f"Error removing values from set in DragonflyDB: {e}")
            return False
    
    def smembers(self, name: str) -> List[str]:
        """
        Get all members of a set in DragonflyDB.
        
        Args:
            name: Set name
            
        Returns:
            List[str]: Members of the set
        """
        try:
            return list(self.client.smembers(name))
        
        except RedisError as e:
            logger.error(f"Error getting members of set in DragonflyDB: {e}")
            return []
    
    def sismember(self, name: str, value: str) -> bool:
        """
        Check if a value is a member of a set in DragonflyDB.
        
        Args:
            name: Set name
            value: Value to check
            
        Returns:
            bool: True if the value is a member of the set, False otherwise
        """
        try:
            return bool(self.client.sismember(name, value))
        
        except RedisError as e:
            logger.error(f"Error checking if value is member of set in DragonflyDB: {e}")
            return False
    
    def scard(self, name: str) -> int:
        """
        Get the number of members in a set in DragonflyDB.
        
        Args:
            name: Set name
            
        Returns:
            int: Number of members in the set
        """
        try:
            return self.client.scard(name)
        
        except RedisError as e:
            logger.error(f"Error getting number of members in set in DragonflyDB: {e}")
            return 0
    
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a JSON value from DragonflyDB.
        
        Args:
            key: Key to get
            
        Returns:
            Optional[Dict[str, Any]]: JSON value for the key, or None if the key does not exist
        """
        try:
            value = self.get(key)
            
            if value is None:
                return None
            
            return json.loads(value)
        
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from DragonflyDB: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting JSON from DragonflyDB: {e}")
            return None
    
    def set_json(self, key: str, value: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """
        Set a JSON value in DragonflyDB.
        
        Args:
            key: Key to set
            value: JSON value to set
            ex: Expiration time in seconds
            
        Returns:
            bool: True if the value was set, False otherwise
        """
        try:
            json_value = json.dumps(value)
            return self.set(key, json_value, ex=ex)
        
        except Exception as e:
            logger.error(f"Error setting JSON in DragonflyDB: {e}")
            return False
    
    def memcached_get(self, key: str) -> Optional[str]:
        """
        Get a value using Memcached protocol.
        
        Args:
            key: Key to get
            
        Returns:
            Optional[str]: Value for the key, or None if the key does not exist
        """
        try:
            return self.get(key)
        
        except Exception as e:
            logger.error(f"Error getting value using Memcached protocol: {e}")
            return None
    
    def memcached_set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set a value using Memcached protocol.
        
        Args:
            key: Key to set
            value: Value to set
            ex: Expiration time in seconds
            
        Returns:
            bool: True if the value was set, False otherwise
        """
        try:
            return self.set(key, value, ex=ex)
        
        except Exception as e:
            logger.error(f"Error setting value using Memcached protocol: {e}")
            return False


dragonfly_client = DragonflyClient()
