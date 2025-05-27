"""
Django management command to test database integration.
"""

import logging
import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test database integration with Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all database integrations, including external services',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Testing Database Integration ==='))
        
        self.test_database_connections()
        
        if options['all']:
            self.test_cache_connection()
            self.test_vector_db_connection()
            self.test_messaging_connection()
            self.test_supabase_auth()
            self.test_supabase_functions()
            self.test_dragonfly_memcached()
        
        self.stdout.write(self.style.SUCCESS('\n=== Database Integration Test Summary ==='))
        self.stdout.write('Database integration tests completed')
        self.stdout.write('Note: Some tests may be skipped in local development environment')
    
    def test_database_connections(self):
        """Test that Django can connect to all configured databases."""
        self.stdout.write('\n=== Testing Database Connections ===')
        
        for db_name in settings.DATABASES.keys():
            self.stdout.write(f'Testing connection to {db_name} database...')
            try:
                with connections[db_name].cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result[0] == 1:
                        self.stdout.write(self.style.SUCCESS(f'✅ Successfully connected to {db_name} database'))
                    else:
                        self.stdout.write(self.style.ERROR(f'❌ Unexpected result from {db_name} database: {result}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error connecting to {db_name} database: {e}'))
    
    def test_cache_connection(self):
        """Test that Django can connect to the cache (DragonflyDB)."""
        self.stdout.write('\n=== Testing Cache Connection (DragonflyDB) ===')
        
        try:
            test_key = f'test_key_{int(time.time())}'
            test_value = 'test_value'
            
            self.stdout.write(f'Setting cache key: {test_key}')
            cache.set(test_key, test_value, 10)
            
            self.stdout.write('Getting cache key')
            value = cache.get(test_key)
            
            if value == test_value:
                self.stdout.write(self.style.SUCCESS(f'✅ Successfully retrieved value from cache: {value}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Unexpected value from cache: {value}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error connecting to cache: {e}'))
            self.stdout.write(self.style.WARNING('⚠️ Cache connection failed, but this is expected in local development'))
    
    def test_vector_db_connection(self):
        """Test that Django can connect to the vector database (RAGflow)."""
        self.stdout.write('\n=== Testing Vector Database Connection (RAGflow) ===')
        
        try:
            from apps.agent.integrations.ragflow import RAGflowClient
            
            self.stdout.write('Initializing RAGflow client')
            client = RAGflowClient()
            
            self.stdout.write('Checking RAGflow health')
            health = client.check_health()
            
            if health['status'] == 'ok':
                self.stdout.write(self.style.SUCCESS(f'✅ RAGflow health check passed: {health}'))
            elif health['status'] == 'mocked':
                self.stdout.write(self.style.WARNING(f'⚠️ RAGflow running in mock mode: {health}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ RAGflow health check failed: {health}'))
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠️ RAGflow client not available'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error connecting to RAGflow: {e}'))
            self.stdout.write(self.style.WARNING('⚠️ RAGflow connection failed, but this is expected in local development'))
    
    def test_messaging_connection(self):
        """Test that Django can connect to the messaging system (RocketMQ)."""
        self.stdout.write('\n=== Testing Messaging Connection (RocketMQ) ===')
        
        try:
            from apps.agent.integrations.rocketmq import RocketMQClient
            
            self.stdout.write('Initializing RocketMQ client')
            client = RocketMQClient()
            
            self.stdout.write('Checking RocketMQ connection')
            status = client.check_connection()
            
            if status['connected']:
                self.stdout.write(self.style.SUCCESS(f'✅ RocketMQ connection check passed: {status}'))
            elif status['mocked']:
                self.stdout.write(self.style.WARNING(f'⚠️ RocketMQ running in mock mode: {status}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ RocketMQ connection check failed: {status}'))
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠️ RocketMQ client not available'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error connecting to RocketMQ: {e}'))
            self.stdout.write(self.style.WARNING('⚠️ RocketMQ connection failed, but this is expected in local development'))
    
    def test_supabase_auth(self):
        """Test Supabase authentication integration."""
        self.stdout.write('\n=== Testing Supabase Authentication ===')
        
        try:
            from apps.agent.integrations.supabase_auth import SupabaseAuth
            
            self.stdout.write('Initializing Supabase Auth client')
            auth = SupabaseAuth()
            
            self.stdout.write('Checking Supabase Auth connection')
            status = auth.check_connection()
            
            if status['connected']:
                self.stdout.write(self.style.SUCCESS(f'✅ Supabase Auth connection check passed: {status}'))
            elif status['mocked']:
                self.stdout.write(self.style.WARNING(f'⚠️ Supabase Auth running in mock mode: {status}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Supabase Auth connection check failed: {status}'))
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠️ Supabase Auth client not available'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error connecting to Supabase Auth: {e}'))
            self.stdout.write(self.style.WARNING('⚠️ Supabase Auth connection failed, but this is expected in local development'))
    
    def test_supabase_functions(self):
        """Test Supabase Functions integration."""
        self.stdout.write('\n=== Testing Supabase Functions ===')
        
        try:
            from apps.agent.integrations.supabase_functions import SupabaseFunctions
            
            self.stdout.write('Initializing Supabase Functions client')
            functions = SupabaseFunctions()
            
            self.stdout.write('Checking Supabase Functions connection')
            status = functions.check_connection()
            
            if status['connected']:
                self.stdout.write(self.style.SUCCESS(f'✅ Supabase Functions connection check passed: {status}'))
            elif status['mocked']:
                self.stdout.write(self.style.WARNING(f'⚠️ Supabase Functions running in mock mode: {status}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Supabase Functions connection check failed: {status}'))
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠️ Supabase Functions client not available'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error connecting to Supabase Functions: {e}'))
            self.stdout.write(self.style.WARNING('⚠️ Supabase Functions connection failed, but this is expected in local development'))
    
    def test_dragonfly_memcached(self):
        """Test DragonflyDB memcached functionality."""
        self.stdout.write('\n=== Testing DragonflyDB Memcached ===')
        
        try:
            from apps.agent.integrations.dragonfly import DragonflyClient
            
            self.stdout.write('Initializing DragonflyDB client')
            client = DragonflyClient()
            
            self.stdout.write('Checking DragonflyDB memcached')
            status = client.check_memcached()
            
            if status['connected']:
                self.stdout.write(self.style.SUCCESS(f'✅ DragonflyDB memcached check passed: {status}'))
            elif status['mocked']:
                self.stdout.write(self.style.WARNING(f'⚠️ DragonflyDB running in mock mode: {status}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ DragonflyDB memcached check failed: {status}'))
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠️ DragonflyDB client not available'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error connecting to DragonflyDB: {e}'))
            self.stdout.write(self.style.WARNING('⚠️ DragonflyDB connection failed, but this is expected in local development'))
