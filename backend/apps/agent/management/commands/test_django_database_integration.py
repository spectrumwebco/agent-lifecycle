"""
Django management command to test database integration with Django.
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test database integration with Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            type=str,
            help='Specify a database to test (supabase, ragflow, dragonfly, rocketmq, doris, postgres)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all database integrations',
        )

    def handle(self, *args, **options):
        if options['all']:
            self.test_all_databases()
        elif options['database']:
            self.test_specific_database(options['database'])
        else:
            self.stdout.write(self.style.WARNING('Please specify a database to test or use --all'))

    def test_all_databases(self):
        """Test all database integrations."""
        self.stdout.write(self.style.SUCCESS('Testing all database integrations...'))
        
        self.test_default_database()
        
        self.test_supabase_databases()
        
        self.test_ragflow_database()
        
        self.test_dragonfly_database()
        
        self.test_rocketmq_database()
        
        self.test_doris_database()
        
        self.test_postgres_database()
        
        self.stdout.write(self.style.SUCCESS('All database tests completed successfully'))

    def test_default_database(self):
        """Test Django's default database."""
        self.stdout.write('Testing Django default database...')
        try:
            connection = connections['default']
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result and result[0] == 1:
                    self.stdout.write(self.style.SUCCESS('Django default database connection successful'))
                else:
                    self.stdout.write(self.style.ERROR('Django default database test failed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Django default database connection failed: {str(e)}'))

    def test_supabase_databases(self):
        """Test Supabase database integration."""
        self.stdout.write('Testing Supabase database integration...')
        try:
            from apps.agent.integrations.supabase import SupabaseClient
            
            client = SupabaseClient()
            auth_result = client.test_auth()
            self.stdout.write(f'Supabase authentication test: {auth_result}')
            
            functions_result = client.test_functions()
            self.stdout.write(f'Supabase functions test: {functions_result}')
            
            storage_result = client.test_storage()
            self.stdout.write(f'Supabase storage test: {storage_result}')
            
            self.stdout.write(self.style.SUCCESS('Supabase integration tests passed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Supabase integration test failed: {str(e)}'))

    def test_ragflow_database(self):
        """Test RAGflow database integration."""
        self.stdout.write('Testing RAGflow database integration...')
        try:
            from apps.agent.integrations.ragflow import RAGflowClient
            
            client = RAGflowClient()
            search_result = client.search("test query")
            self.stdout.write(f'RAGflow search test: {search_result}')
            
            embedding_result = client.get_embedding("test text")
            self.stdout.write(f'RAGflow embedding test: {embedding_result}')
            
            self.stdout.write(self.style.SUCCESS('RAGflow integration tests passed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'RAGflow integration test failed: {str(e)}'))

    def test_dragonfly_database(self):
        """Test DragonflyDB integration."""
        self.stdout.write('Testing DragonflyDB integration...')
        try:
            from apps.agent.integrations.dragonfly import DragonflyClient
            
            client = DragonflyClient()
            kv_result = client.test_kv_operations()
            self.stdout.write(f'DragonflyDB key-value test: {kv_result}')
            
            memcached_result = client.test_memcached_operations()
            self.stdout.write(f'DragonflyDB memcached test: {memcached_result}')
            
            self.stdout.write(self.style.SUCCESS('DragonflyDB integration tests passed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'DragonflyDB integration test failed: {str(e)}'))

    def test_rocketmq_database(self):
        """Test RocketMQ integration."""
        self.stdout.write('Testing RocketMQ integration...')
        try:
            from apps.agent.integrations.rocketmq import RocketMQClient
            
            client = RocketMQClient()
            producer_result = client.create_producer("test_topic")
            self.stdout.write(f'RocketMQ producer test: {producer_result}')
            
            def callback(topic, message):
                self.stdout.write(f'RocketMQ consumer received message: {message}')
                return True
            
            consumer_result = client.create_consumer("test_topic", callback)
            self.stdout.write(f'RocketMQ consumer test: {consumer_result}')
            
            message_result = client.send_message("test_topic", "test message")
            self.stdout.write(f'RocketMQ message sending test: {message_result}')
            
            self.stdout.write(self.style.SUCCESS('RocketMQ integration tests passed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'RocketMQ integration test failed: {str(e)}'))

    def test_doris_database(self):
        """Test Apache Doris integration."""
        self.stdout.write('Testing Apache Doris integration...')
        try:
            from apps.agent.integrations.doris import DorisClient
            
            client = DorisClient()
            query_result = client.execute_query("SELECT 1")
            self.stdout.write(f'Apache Doris query test: {query_result}')
            
            table_result = client.test_table_operations()
            self.stdout.write(f'Apache Doris table operations test: {table_result}')
            
            self.stdout.write(self.style.SUCCESS('Apache Doris integration tests passed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Apache Doris integration test failed: {str(e)}'))

    def test_postgres_database(self):
        """Test PostgreSQL integration."""
        self.stdout.write('Testing PostgreSQL integration...')
        try:
            from apps.agent.integrations.crunchydata import PostgresOperatorClient
            
            client = PostgresOperatorClient()
            status_result = client.get_cluster_status()
            self.stdout.write(f'PostgreSQL cluster status test: {status_result}')
            
            query_result = client.execute_query("SELECT 1")
            self.stdout.write(f'PostgreSQL query test: {query_result}')
            
            self.stdout.write(self.style.SUCCESS('PostgreSQL integration tests passed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'PostgreSQL integration test failed: {str(e)}'))

    def test_specific_database(self, database):
        """Test a specific database integration."""
        if database == 'supabase':
            self.test_supabase_databases()
        elif database == 'ragflow':
            self.test_ragflow_database()
        elif database == 'dragonfly':
            self.test_dragonfly_database()
        elif database == 'rocketmq':
            self.test_rocketmq_database()
        elif database == 'doris':
            self.test_doris_database()
        elif database == 'postgres':
            self.test_postgres_database()
        else:
            self.stdout.write(self.style.ERROR(f'Unknown database: {database}'))
