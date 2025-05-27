"""
Management command to test database integration with mock databases for local development.
"""

import os
import sys
import logging
import json
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test database integration with mock databases for local development'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Test all database integrations')
        parser.add_argument('--supabase', action='store_true', help='Test Supabase integration')
        parser.add_argument('--ragflow', action='store_true', help='Test RAGflow integration')
        parser.add_argument('--dragonfly', action='store_true', help='Test DragonflyDB integration')
        parser.add_argument('--rocketmq', action='store_true', help='Test RocketMQ integration')
        parser.add_argument('--doris', action='store_true', help='Test Apache Doris integration')
        parser.add_argument('--postgres', action='store_true', help='Test PostgreSQL integration')
        parser.add_argument('--kafka', action='store_true', help='Test Kafka integration')

    def handle(self, *args, **options):
        """
        Handle the command execution.
        """
        self.stdout.write(self.style.SUCCESS('Testing database integration with mock databases'))
        
        run_all = options['all'] or not any([
            options['supabase'], options['ragflow'], options['dragonfly'], 
            options['rocketmq'], options['doris'], options['postgres'], options['kafka']
        ])
        
        success = True
        
        if run_all or options['supabase']:
            if not self.test_supabase():
                success = False
        
        if run_all or options['ragflow']:
            if not self.test_ragflow():
                success = False
        
        if run_all or options['dragonfly']:
            if not self.test_dragonfly():
                success = False
        
        if run_all or options['rocketmq']:
            if not self.test_rocketmq():
                success = False
        
        if run_all or options['doris']:
            if not self.test_doris():
                success = False
        
        if run_all or options['postgres']:
            if not self.test_postgres():
                success = False
        
        if run_all or options['kafka']:
            if not self.test_kafka():
                success = False
        
        if success:
            self.stdout.write(self.style.SUCCESS('All database integration tests passed'))
        else:
            self.stdout.write(self.style.ERROR('Some database integration tests failed'))
            sys.exit(1)
    
    def test_supabase(self):
        """
        Test Supabase integration with mock database.
        """
        self.stdout.write('Testing Supabase integration...')
        
        try:
            from apps.agent.integrations.supabase import SupabaseClient
            
            client = SupabaseClient(url="mock://supabase", key="mock-key")
            
            self.stdout.write('  Testing query operations...')
            records = client.query_table('test_table')
            self.stdout.write(f'  Query result: {records}')
            
            self.stdout.write('  Testing insert operations...')
            record = client.insert_record('test_table', {'name': 'Test Record'})
            self.stdout.write(f'  Insert result: {record}')
            
            self.stdout.write(self.style.SUCCESS('  Supabase integration test passed'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Supabase integration test failed: {e}'))
            return False
    
    def test_ragflow(self):
        """
        Test RAGflow integration with mock database.
        """
        self.stdout.write('Testing RAGflow integration...')
        
        try:
            from apps.agent.integrations.ragflow import RAGflowClient
            
            client = RAGflowClient(host="localhost", port=8000, api_key="mock-key")
            
            self.stdout.write('  Testing search functionality...')
            results = client.search("test query")
            self.stdout.write(f'  Search result: {results}')
            
            self.stdout.write('  Testing semantic search functionality...')
            results = client.semantic_search("test query")
            self.stdout.write(f'  Semantic search result: {results}')
            
            self.stdout.write(self.style.SUCCESS('  RAGflow integration test passed'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  RAGflow integration test failed: {e}'))
            return False
    
    def test_dragonfly(self):
        """
        Test DragonflyDB integration with mock database.
        """
        self.stdout.write('Testing DragonflyDB integration...')
        
        try:
            from apps.agent.integrations.dragonfly import DragonflyClient
            
            client = DragonflyClient(host="localhost", port=6379, mock=True)
            
            self.stdout.write('  Testing key-value operations...')
            client.set("test_key", "test_value")
            value = client.get("test_key")
            self.stdout.write(f'  Get result: {value}')
            
            self.stdout.write('  Testing memcached operations...')
            client.memcached_set("test_memcached_key", "test_memcached_value")
            value = client.memcached_get("test_memcached_key")
            self.stdout.write(f'  Memcached get result: {value}')
            
            self.stdout.write(self.style.SUCCESS('  DragonflyDB integration test passed'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  DragonflyDB integration test failed: {e}'))
            return False
    
    def test_rocketmq(self):
        """
        Test RocketMQ integration with mock database.
        """
        self.stdout.write('Testing RocketMQ integration...')
        
        try:
            from apps.agent.integrations.rocketmq import RocketMQClient
            
            client = RocketMQClient(host="localhost", port=9876, mock=True)
            
            self.stdout.write('  Testing message production and consumption...')
            message_id = client.send_message("test_topic", {"test": "message"})
            self.stdout.write(f'  Message ID: {message_id}')
            
            message = client.consume_message("test_topic")
            self.stdout.write(f'  Consumed message: {message}')
            
            self.stdout.write('  Testing state management...')
            client.update_state("test_state", {"status": "testing"})
            state = client.get_state("test_state")
            self.stdout.write(f'  State: {state}')
            
            self.stdout.write(self.style.SUCCESS('  RocketMQ integration test passed'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  RocketMQ integration test failed: {e}'))
            return False
    
    def test_doris(self):
        """
        Test Apache Doris integration with mock database.
        """
        self.stdout.write('Testing Apache Doris integration...')
        
        try:
            from apps.agent.integrations.doris import DorisClient
            
            client = DorisClient(host="localhost", port=9030, user="root", password="", mock=True)
            
            self.stdout.write('  Testing query execution...')
            results = client.execute_query("SELECT 1")
            self.stdout.write(f'  Query result: {results}')
            
            self.stdout.write('  Testing table operations...')
            client.create_table("test_table", {
                "id": "INT",
                "name": "VARCHAR(100)",
                "created_at": "DATETIME"
            })
            
            client.insert_data("test_table", [
                {"id": 1, "name": "Test 1", "created_at": "2023-01-01 00:00:00"},
                {"id": 2, "name": "Test 2", "created_at": "2023-01-02 00:00:00"}
            ])
            
            results = client.execute_query("SELECT * FROM test_table")
            self.stdout.write(f'  Table data: {results}')
            
            self.stdout.write(self.style.SUCCESS('  Apache Doris integration test passed'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Apache Doris integration test failed: {e}'))
            return False
    
    def test_postgres(self):
        """
        Test PostgreSQL integration with mock database.
        """
        self.stdout.write('Testing PostgreSQL integration...')
        
        try:
            from apps.agent.integrations.crunchydata import PostgresClient
            
            client = PostgresClient(host="localhost", port=5432, user="postgres", password="", mock=True)
            
            self.stdout.write('  Testing query execution...')
            results = client.execute_query("SELECT 1")
            self.stdout.write(f'  Query result: {results}')
            
            self.stdout.write('  Testing table operations...')
            client.create_table("test_table", {
                "id": "SERIAL PRIMARY KEY",
                "name": "VARCHAR(100)",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            })
            
            client.insert_data("test_table", [
                {"name": "Test 1"},
                {"name": "Test 2"}
            ])
            
            results = client.execute_query("SELECT * FROM test_table")
            self.stdout.write(f'  Table data: {results}')
            
            self.stdout.write(self.style.SUCCESS('  PostgreSQL integration test passed'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  PostgreSQL integration test failed: {e}'))
            return False
    
    def test_kafka(self):
        """
        Test Kafka integration with mock database.
        """
        self.stdout.write('Testing Kafka integration...')
        
        try:
            from apps.agent.integrations.kafka import KafkaClient
            
            client = KafkaClient(bootstrap_servers="localhost:9092", mock=True)
            
            self.stdout.write('  Testing message production and consumption...')
            client.produce_message("test_topic", {"test": "message"})
            
            message = client.consume_message("test_topic")
            self.stdout.write(f'  Consumed message: {message}')
            
            self.stdout.write(self.style.SUCCESS('  Kafka integration test passed'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Kafka integration test failed: {e}'))
            return False
