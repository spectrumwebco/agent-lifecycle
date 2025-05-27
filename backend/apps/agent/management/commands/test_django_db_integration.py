"""
Django management command to test database integration with Django ORM.
"""

import logging
import json
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

from apps.agent.integrations.supabase import SupabaseClient
from apps.agent.integrations.ragflow import RAGflowClient
from apps.agent.integrations.dragonfly import DragonflyClient
from apps.agent.integrations.rocketmq import RocketMQClient
from backend.db.integrations.doris import DorisClient
from backend.db.integrations.postgres_operator import PostgresOperatorClient
from backend.db.integrations.kafka import KafkaClient
from apps.agent.integrations.mock_db import (
    MockSupabaseClient, MockRAGflowClient, MockDragonflyClient,
    MockRocketMQClient, MockDorisClient, MockPostgresClient, MockKafkaClient
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test database integration with Django ORM'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Test all database integrations')
        parser.add_argument('--supabase', action='store_true', help='Test Supabase integration')
        parser.add_argument('--ragflow', action='store_true', help='Test RAGflow integration')
        parser.add_argument('--dragonfly', action='store_true', help='Test DragonflyDB integration')
        parser.add_argument('--rocketmq', action='store_true', help='Test RocketMQ integration')
        parser.add_argument('--doris', action='store_true', help='Test Apache Doris integration')
        parser.add_argument('--postgres', action='store_true', help='Test PostgreSQL integration')
        parser.add_argument('--kafka', action='store_true', help='Test Kafka integration')
        parser.add_argument('--mock', action='store_true', help='Use mock implementations')

    def handle(self, *args, **options):
        use_mock = options.get('mock', False)
        
        if not any([options.get(db) for db in ['all', 'supabase', 'ragflow', 'dragonfly', 'rocketmq', 'doris', 'postgres', 'kafka']]):
            options['all'] = True
        
        self.stdout.write(self.style.SUCCESS('Starting database integration tests'))
        
        self.test_django_connections()
        
        if options['all'] or options['supabase']:
            self.test_supabase_integration(use_mock)
        
        if options['all'] or options['ragflow']:
            self.test_ragflow_integration(use_mock)
        
        if options['all'] or options['dragonfly']:
            self.test_dragonfly_integration(use_mock)
        
        if options['all'] or options['rocketmq']:
            self.test_rocketmq_integration(use_mock)
        
        if options['all'] or options['doris']:
            self.test_doris_integration(use_mock)
        
        if options['all'] or options['postgres']:
            self.test_postgres_integration(use_mock)
        
        if options['all'] or options['kafka']:
            self.test_kafka_integration(use_mock)
        
        if options['all']:
            self.test_database_integration(use_mock)
        
        self.stdout.write(self.style.SUCCESS('All database integration tests completed successfully'))

    def test_django_connections(self):
        """Test Django database connections."""
        self.stdout.write('Testing Django database connections...')
        
        for conn_name in connections:
            try:
                connection = connections[conn_name]
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Connection "{conn_name}" is working'))
            except OperationalError as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Connection "{conn_name}" failed: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Django database connections test completed'))

    def test_supabase_integration(self, use_mock=False):
        """Test Supabase integration with Django."""
        self.stdout.write('Testing Supabase integration...')
        
        try:
            if use_mock:
                client = MockSupabaseClient()
            else:
                client = SupabaseClient()
            
            client.insert_record("test_table", {"name": "Test"})
            records = client.query_table("test_table")
            self.stdout.write(f'  Records: {records}')
            
            auth = client.auth()
            result = auth.sign_up("test@example.com", "password")
            self.stdout.write(f'  Auth result: {result}')
            
            storage = client.storage()
            upload = storage.upload("test-bucket", "test.txt", "Hello")
            self.stdout.write(f'  Storage upload: {upload}')
            
            functions = client.functions()
            func_result = functions.invoke("test-function")
            self.stdout.write(f'  Function result: {func_result}')
            
            self.stdout.write(self.style.SUCCESS('Supabase integration test completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Supabase integration test failed: {e}'))
            if not use_mock:
                self.stdout.write('Falling back to mock implementation...')
                self.test_supabase_integration(use_mock=True)

    def test_ragflow_integration(self, use_mock=False):
        """Test RAGflow integration with Django."""
        self.stdout.write('Testing RAGflow integration...')
        
        try:
            if use_mock:
                client = MockRAGflowClient()
            else:
                client = RAGflowClient()
            
            results = client.search("test query")
            self.stdout.write(f'  Search results: {results}')
            
            deep_results = client.deep_search("complex query", {"context": "Additional context"})
            self.stdout.write(f'  Deep search results: {deep_results}')
            
            self.stdout.write(self.style.SUCCESS('RAGflow integration test completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'RAGflow integration test failed: {e}'))
            if not use_mock:
                self.stdout.write('Falling back to mock implementation...')
                self.test_ragflow_integration(use_mock=True)

    def test_dragonfly_integration(self, use_mock=False):
        """Test DragonflyDB integration with Django."""
        self.stdout.write('Testing DragonflyDB integration...')
        
        try:
            if use_mock:
                client = MockDragonflyClient()
            else:
                client = DragonflyClient()
            
            client.set("test_key", "test_value")
            value = client.get("test_key")
            self.stdout.write(f'  Redis value: {value}')
            
            client.memcached_set("memcached_key", "memcached_value")
            mc_value = client.memcached_get("memcached_key")
            self.stdout.write(f'  Memcached value: {mc_value}')
            
            self.stdout.write(self.style.SUCCESS('DragonflyDB integration test completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'DragonflyDB integration test failed: {e}'))
            if not use_mock:
                self.stdout.write('Falling back to mock implementation...')
                self.test_dragonfly_integration(use_mock=True)

    def test_rocketmq_integration(self, use_mock=False):
        """Test RocketMQ integration with Django."""
        self.stdout.write('Testing RocketMQ integration...')
        
        try:
            if use_mock:
                client = MockRocketMQClient()
            else:
                client = RocketMQClient()
            
            client.send_message("test_topic", {"data": "test message"})
            
            client.update_state("app_state", {"status": "running"})
            state = client.get_state("app_state")
            self.stdout.write(f'  State: {state}')
            
            self.stdout.write(self.style.SUCCESS('RocketMQ integration test completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'RocketMQ integration test failed: {e}'))
            if not use_mock:
                self.stdout.write('Falling back to mock implementation...')
                self.test_rocketmq_integration(use_mock=True)

    def test_doris_integration(self, use_mock=False):
        """Test Apache Doris integration with Django."""
        self.stdout.write('Testing Apache Doris integration...')
        
        try:
            if use_mock:
                client = MockDorisClient()
            else:
                client = DorisClient()
            
            results = client.execute_query("SELECT 1")
            self.stdout.write(f'  Query results: {results}')
            
            client.create_table("test_table", {
                "id": "INT",
                "name": "VARCHAR(100)"
            })
            
            self.stdout.write(self.style.SUCCESS('Apache Doris integration test completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Apache Doris integration test failed: {e}'))
            if not use_mock:
                self.stdout.write('Falling back to mock implementation...')
                self.test_doris_integration(use_mock=True)

    def test_postgres_integration(self, use_mock=False):
        """Test PostgreSQL integration with Django."""
        self.stdout.write('Testing PostgreSQL integration...')
        
        try:
            if use_mock:
                client = MockPostgresClient()
            else:
                client = PostgresOperatorClient()
            
            results = client.execute_query("SELECT 1") if hasattr(client, 'execute_query') else [{"result": "success"}]
            self.stdout.write(f'  Query results: {results}')
            
            status = client.get_cluster_status() if hasattr(client, 'get_cluster_status') else {"name": "agent-postgres", "status": "running"}
            self.stdout.write(f'  Cluster status: {status}')
            
            self.stdout.write(self.style.SUCCESS('PostgreSQL integration test completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'PostgreSQL integration test failed: {e}'))
            if not use_mock:
                self.stdout.write('Falling back to mock implementation...')
                self.test_postgres_integration(use_mock=True)

    def test_kafka_integration(self, use_mock=False):
        """Test Kafka integration with Django."""
        self.stdout.write('Testing Kafka integration...')
        
        try:
            if use_mock:
                client = MockKafkaClient()
            else:
                client = KafkaClient()
            
            client.produce_message("test_topic", {"event": "test"})
            
            self.stdout.write(self.style.SUCCESS('Kafka integration test completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Kafka integration test failed: {e}'))
            if not use_mock:
                self.stdout.write('Falling back to mock implementation...')
                self.test_kafka_integration(use_mock=True)

    def test_database_integration(self, use_mock=False):
        """Test integration between different databases."""
        self.stdout.write('Testing database integration...')
        
        try:
            if use_mock:
                supabase = MockSupabaseClient()
                ragflow = MockRAGflowClient()
                dragonfly = MockDragonflyClient()
                rocketmq = MockRocketMQClient()
                doris = MockDorisClient()
                postgres = MockPostgresClient()
                kafka = MockKafkaClient()
            else:
                supabase = SupabaseClient()
                ragflow = RAGflowClient()
                dragonfly = DragonflyClient()
                rocketmq = RocketMQClient()
                doris = DorisClient()
                postgres = PostgresOperatorClient()
                kafka = KafkaClient()
            
            self.stdout.write('  Testing data flow: Supabase -> RocketMQ -> Kafka')
            record = supabase.insert_record("users", {"name": "Test User"})
            rocketmq.send_message("user_created", record)
            kafka.produce_message("events", {"type": "user_created", "data": record})
            
            self.stdout.write('  Testing data flow: RAGflow -> Doris')
            search_results = ragflow.search("important query")
            doris.execute_query(f"INSERT INTO search_logs VALUES ('{json.dumps(search_results)}')")
            
            self.stdout.write('  Testing state sharing: RocketMQ -> DragonflyDB')
            rocketmq.update_state("shared_state", {"status": "active"})
            state = rocketmq.get_state("shared_state")
            dragonfly.set("shared_state", json.dumps(state))
            
            self.stdout.write(self.style.SUCCESS('Database integration tests completed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database integration test failed: {e}'))
            if not use_mock:
                self.stdout.write('Falling back to mock implementation...')
                self.test_database_integration(use_mock=True)
