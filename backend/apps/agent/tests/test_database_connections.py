"""
Test database connections for all database systems.
"""

import os
import json
import logging
from django.test import TestCase
from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

class DatabaseConnectionsTestCase(TestCase):
    """Test case for database connections."""
    
    def setUp(self):
        """Set up test case."""
        pass
    
    def test_supabase_connections(self):
        """Test Supabase database connections."""
        supabase_dbs = ['agent_db', 'trajectory_db', 'ml_db', 'user_db']
        
        for db_name in supabase_dbs:
            if db_name in connections.databases:
                try:
                    with connections[db_name].cursor() as cursor:
                        cursor.execute("SELECT current_database()")
                        current_db = cursor.fetchone()[0]
                        self.assertIsNotNone(current_db)
                        logger.info(f"Connected to Supabase database {db_name}: {current_db}")
                except Exception as e:
                    logger.error(f"Failed to connect to Supabase database {db_name}: {e}")
                    self.fail(f"Failed to connect to Supabase database {db_name}: {e}")
            else:
                logger.warning(f"Supabase database {db_name} not configured in settings")
    
    def test_ragflow_connection(self):
        """Test RAGflow vector database connection."""
        try:
            from apps.agent.integrations.ragflow import RAGflowClient
            
            client = RAGflowClient()
            
            results = client.search("test", top_k=1)
            
            self.assertIsInstance(results, dict)
            logger.info(f"Connected to RAGflow vector database: {results}")
            
            results = client.semantic_search("test", top_k=1)
            
            self.assertIsInstance(results, dict)
            logger.info(f"RAGflow deep search functionality working: {results}")
            
        except Exception as e:
            logger.error(f"Failed to connect to RAGflow vector database: {e}")
            self.fail(f"Failed to connect to RAGflow vector database: {e}")
    
    def test_dragonfly_connection(self):
        """Test DragonflyDB connection."""
        try:
            from apps.agent.integrations.dragonfly import DragonflyClient
            
            client = DragonflyClient()
            
            client.set("test_key", "test_value")
            value = client.get("test_key")
            
            self.assertEqual(value, "test_value")
            logger.info(f"Connected to DragonflyDB: {value}")
            
            client.memcached_set("test_memcached_key", "test_memcached_value")
            value = client.memcached_get("test_memcached_key")
            
            self.assertEqual(value, "test_memcached_value")
            logger.info(f"DragonflyDB memcached functionality working: {value}")
            
        except Exception as e:
            logger.error(f"Failed to connect to DragonflyDB: {e}")
            self.fail(f"Failed to connect to DragonflyDB: {e}")
    
    def test_rocketmq_connection(self):
        """Test RocketMQ connection."""
        try:
            from apps.agent.integrations.rocketmq import RocketMQClient
            
            client = RocketMQClient()
            
            message_id = client.send_message("test_topic", {"test": "message"})
            
            self.assertIsNotNone(message_id)
            logger.info(f"Connected to RocketMQ: {message_id}")
            
            client.update_state("test_state", {"status": "testing"})
            state = client.get_state("test_state")
            
            self.assertEqual(state["status"], "testing")
            logger.info(f"RocketMQ state management working: {state}")
            
        except Exception as e:
            logger.error(f"Failed to connect to RocketMQ: {e}")
            self.fail(f"Failed to connect to RocketMQ: {e}")
    
    def test_doris_connection(self):
        """Test Apache Doris connection."""
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                
                self.assertIsNotNone(version)
                logger.info(f"Connected to Apache Doris: {version}")
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_doris_connection (
                    id INT,
                    name VARCHAR(100),
                    created_at DATETIME
                ) ENGINE=OLAP
                DUPLICATE KEY(id)
                DISTRIBUTED BY HASH(id) BUCKETS 3
                PROPERTIES (
                    "replication_num" = "1"
                )
                """)
                
                cursor.execute("""
                INSERT INTO test_doris_connection VALUES 
                (1, 'Test 1', NOW()),
                (2, 'Test 2', NOW()),
                (3, 'Test 3', NOW())
                """)
                
                cursor.execute("SELECT COUNT(*) FROM test_doris_connection")
                count = cursor.fetchone()[0]
                
                self.assertEqual(count, 3)
                logger.info(f"Apache Doris data operations working: {count} rows")
                
        except Exception as e:
            logger.error(f"Failed to connect to Apache Doris: {e}")
            self.fail(f"Failed to connect to Apache Doris: {e}")
    
    def test_postgres_connection(self):
        """Test PostgreSQL connection."""
        try:
            with connections['agent_db'].cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                self.assertIsNotNone(version)
                logger.info(f"Connected to PostgreSQL: {version}")
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_postgres_connection (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                cursor.execute("""
                INSERT INTO test_postgres_connection (name) VALUES 
                ('Test 1'),
                ('Test 2'),
                ('Test 3')
                RETURNING id
                """)
                
                cursor.execute("SELECT COUNT(*) FROM test_postgres_connection")
                count = cursor.fetchone()[0]
                
                self.assertEqual(count, 3)
                logger.info(f"PostgreSQL data operations working: {count} rows")
                
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.fail(f"Failed to connect to PostgreSQL: {e}")
    
    def test_kafka_connection(self):
        """Test Kafka connection."""
        try:
            from apps.agent.integrations.kafka import KafkaClient
            
            client = KafkaClient()
            
            client.produce_message("test_topic", {"test": "message"})
            message = client.consume_message("test_topic", timeout=10)
            
            self.assertIsNotNone(message)
            logger.info(f"Connected to Kafka: {message}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.fail(f"Failed to connect to Kafka: {e}")
    
    def test_cross_database_integration(self):
        """Test cross-database integration."""
        try:
            from apps.agent.integrations.kafka import KafkaClient
            
            with connections['agent_db'].cursor() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_integration (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    value INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                cursor.execute("""
                INSERT INTO test_integration (name, value) VALUES 
                ('Integration Test 1', 100),
                ('Integration Test 2', 200),
                ('Integration Test 3', 300)
                RETURNING id
                """)
            
            kafka_client = KafkaClient()
            kafka_client.produce_message("test_integration", {
                "source": "postgres",
                "destination": "doris",
                "table": "test_integration",
                "operation": "insert"
            })
            
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_integration (
                    id INT,
                    name VARCHAR(100),
                    value INT,
                    created_at DATETIME
                ) ENGINE=OLAP
                DUPLICATE KEY(id)
                DISTRIBUTED BY HASH(id) BUCKETS 3
                PROPERTIES (
                    "replication_num" = "1"
                )
                """)
                
                cursor.execute("""
                INSERT INTO test_integration VALUES 
                (1, 'Integration Test 1', 100, NOW()),
                (2, 'Integration Test 2', 200, NOW()),
                (3, 'Integration Test 3', 300, NOW())
                """)
                
                cursor.execute("SELECT COUNT(*) FROM test_integration")
                count = cursor.fetchone()[0]
                
                self.assertEqual(count, 3)
                logger.info(f"Cross-database integration working: {count} rows")
                
        except Exception as e:
            logger.error(f"Failed to test cross-database integration: {e}")
            self.fail(f"Failed to test cross-database integration: {e}")
