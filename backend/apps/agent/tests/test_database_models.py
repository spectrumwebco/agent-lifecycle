"""
Test database models integration with Django ORM.
"""

from django.test import TestCase
from django.db import connections
from django.conf import settings
import json
import time
import logging

logger = logging.getLogger(__name__)

from apps.agent.models.agent_models import AgentConfig, AgentSession
from apps.agent.models.trajectory_models import Trajectory, TrajectoryStep
from apps.agent.models.ml_models import MLModel, MLPrediction

class DorisIntegrationTest(TestCase):
    """Test Apache Doris integration with Django ORM."""
    
    databases = ['default']
    
    def setUp(self):
        """Set up test environment."""
        with connections['default'].cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_doris_django (
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
    
    def test_doris_connection(self):
        """Test connection to Apache Doris."""
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            self.assertIsNotNone(version)
            logger.info(f"Connected to Apache Doris: {version}")
    
    def test_doris_crud_operations(self):
        """Test CRUD operations on Apache Doris."""
        with connections['default'].cursor() as cursor:
            cursor.execute("""
            INSERT INTO test_doris_django VALUES 
            (1, 'Test 1', NOW()),
            (2, 'Test 2', NOW()),
            (3, 'Test 3', NOW())
            """)
            
            cursor.execute("SELECT COUNT(*) FROM test_doris_django")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 3)
            
            cursor.execute("UPDATE test_doris_django SET name = 'Updated Test' WHERE id = 1")
            
            cursor.execute("SELECT name FROM test_doris_django WHERE id = 1")
            name = cursor.fetchone()[0]
            self.assertEqual(name, 'Updated Test')
            
            cursor.execute("DELETE FROM test_doris_django WHERE id = 3")
            
            cursor.execute("SELECT COUNT(*) FROM test_doris_django")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 2)


class PostgresIntegrationTest(TestCase):
    """Test PostgreSQL integration with Django ORM."""
    
    databases = ['agent_db']
    
    def setUp(self):
        """Set up test environment."""
        AgentConfig.objects.create(
            name="Test Config",
            config_type="test",
            config_data={"test": "data"}
        )
        
        AgentSession.objects.create(
            session_id="test-session",
            agent_config_id=1,
            status="active"
        )
    
    def test_postgres_connection(self):
        """Test connection to PostgreSQL."""
        with connections['agent_db'].cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            self.assertIsNotNone(version)
            logger.info(f"Connected to PostgreSQL: {version}")
    
    def test_postgres_orm_operations(self):
        """Test ORM operations on PostgreSQL."""
        config = AgentConfig.objects.create(
            name="Test Config 2",
            config_type="test",
            config_data={"test": "data2"}
        )
        self.assertIsNotNone(config.id)
        
        retrieved_config = AgentConfig.objects.get(id=config.id)
        self.assertEqual(retrieved_config.name, "Test Config 2")
        
        retrieved_config.name = "Updated Config"
        retrieved_config.save()
        
        updated_config = AgentConfig.objects.get(id=config.id)
        self.assertEqual(updated_config.name, "Updated Config")
        
        retrieved_config.delete()
        
        with self.assertRaises(AgentConfig.DoesNotExist):
            AgentConfig.objects.get(id=config.id)
    
    def test_agent_session_relationship(self):
        """Test relationship between AgentConfig and AgentSession."""
        config = AgentConfig.objects.create(
            name="Relationship Test",
            config_type="test",
            config_data={"test": "relationship"}
        )
        
        session = AgentSession.objects.create(
            session_id="relationship-test",
            agent_config=config,
            status="active"
        )
        
        self.assertEqual(session.agent_config.name, "Relationship Test")
        
        self.assertEqual(config.agent_sessions.first().session_id, "relationship-test")


class KafkaIntegrationTest(TestCase):
    """Test Kafka integration with Django."""
    
    def test_kafka_connection(self):
        """Test connection to Kafka."""
        try:
            from confluent_kafka import Producer, Consumer, KafkaError
            
            kafka_config = getattr(settings, 'KAFKA_CONFIG', {})
            bootstrap_servers = kafka_config.get('bootstrap_servers', 'kafka.default.svc.cluster.local:9092')
            
            producer_conf = {
                'bootstrap.servers': bootstrap_servers,
                'client.id': 'django-test-producer'
            }
            producer = Producer(producer_conf)
            
            test_topic = 'test_kafka_django_integration'
            
            test_message = {
                'id': 1,
                'message': 'Test Kafka Django integration',
                'timestamp': time.time()
            }
            producer.produce(test_topic, json.dumps(test_message).encode('utf-8'))
            producer.flush()
            
            consumer_conf = {
                'bootstrap.servers': bootstrap_servers,
                'group.id': 'django-test-consumer',
                'auto.offset.reset': 'earliest'
            }
            consumer = Consumer(consumer_conf)
            consumer.subscribe([test_topic])
            
            msg = consumer.poll(timeout=10.0)
            
            self.assertIsNotNone(msg)
            self.assertFalse(msg.error())
            
            received_message = json.loads(msg.value().decode('utf-8'))
            self.assertEqual(received_message['message'], 'Test Kafka Django integration')
            
            consumer.close()
            
        except ImportError:
            self.skipTest("Kafka libraries not installed")


class IntegratedDatabaseTest(TestCase):
    """Test integration between all database systems."""
    
    databases = ['default', 'agent_db', 'trajectory_db', 'ml_db']
    
    def setUp(self):
        """Set up test environment."""
        self.agent_config = AgentConfig.objects.create(
            name="Integration Test Config",
            config_type="integration_test",
            config_data={"test": "integration"}
        )
        
        self.agent_session = AgentSession.objects.create(
            session_id="integration-test-session",
            agent_config=self.agent_config,
            status="active"
        )
        
        self.trajectory = Trajectory.objects.create(
            trajectory_id="integration-test-trajectory",
            agent_session_id=self.agent_session.id,
            status="active"
        )
        
        self.ml_model = MLModel.objects.create(
            model_name="integration-test-model",
            model_type="test",
            model_version="1.0.0"
        )
    
    def test_cross_database_queries(self):
        """Test queries across multiple databases."""
        agent_config = AgentConfig.objects.get(id=self.agent_config.id)
        self.assertEqual(agent_config.name, "Integration Test Config")
        
        trajectory = Trajectory.objects.get(trajectory_id="integration-test-trajectory")
        self.assertEqual(trajectory.status, "active")
        
        ml_model = MLModel.objects.get(model_name="integration-test-model")
        self.assertEqual(ml_model.model_version, "1.0.0")
    
    def test_data_flow_between_databases(self):
        """Test data flow between databases."""
        trajectory_step = TrajectoryStep.objects.create(
            trajectory=self.trajectory,
            step_number=1,
            action_type="test",
            action_data={"session_id": self.agent_session.session_id}
        )
        
        ml_prediction = MLPrediction.objects.create(
            ml_model=self.ml_model,
            input_data={"trajectory_step_id": trajectory_step.id},
            output_data={"prediction": "test"},
            confidence=0.95
        )
        
        self.assertEqual(trajectory_step.trajectory.agent_session_id, self.agent_session.id)
        self.assertEqual(ml_prediction.ml_model.model_name, "integration-test-model")
        
        with connections['trajectory_db'].cursor() as cursor:
            cursor.execute(f"SELECT id FROM trajectory_step WHERE id = {trajectory_step.id}")
            step_id = cursor.fetchone()[0]
            self.assertEqual(step_id, trajectory_step.id)
        
        with connections['ml_db'].cursor() as cursor:
            cursor.execute(f"SELECT id FROM ml_prediction WHERE id = {ml_prediction.id}")
            prediction_id = cursor.fetchone()[0]
            self.assertEqual(prediction_id, ml_prediction.id)
